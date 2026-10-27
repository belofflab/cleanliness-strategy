"""Бизнес-логика заказов: смена статуса с валидацией, назначение клинера, уведомления.

Используется и мобайлом (клинер двигает статус), и админ-CRM (менеджер
назначает мастера / отменяет заказ / конвертирует лид). Каждое значимое
изменение пишет уведомление пользователю — это и есть история пушей в профиле.

Все многошаговые изменения выполняются как одна единица работы
(`app.core.db.transaction`): статус + уведомление, назначение + статус +
уведомление, заказ из лида + статус лида — либо всё, либо ничего.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import transaction
from app.core.errors import DomainError
from app.models.notifications import NOTIFY_ORDER_ASSIGNED, NOTIFY_ORDER_STATUS
from app.models.orders import (
    LEAD_CONVERTED,
    ORDER_ASSIGNED,
    ORDER_DONE,
    ORDER_NEW,
    ORDER_TRANSITIONS,
    Lead,
    Order,
)
from app.modules.identity import repository as users_repo
from app.modules.orders import repository as orders_repo
from app.modules.pricing.quoting import QuotingError, build_quote
from app.repositories import booking as booking_repo
from app.repositories import leads as leads_repo
from app.repositories import notifications as notifications_repo

__all__ = [
    "STATUS_LABELS",
    "OrderError",
    "assign_master",
    "change_status",
    "convert_lead_to_order",
]

logger = logging.getLogger(__name__)

# Человекочитаемые подписи статусов для уведомлений.
STATUS_LABELS = {
    "new": "Новый",
    "assigned": "Назначен мастер",
    "in_progress": "Уборка началась",
    "done": "Уборка завершена",
    "cancelled": "Заказ отменён",
}


class OrderError(DomainError):
    status_code = 400
    code = "order_error"


async def change_status(
    db: AsyncSession, order: Order, new_status: str, *, notify: bool = True
) -> Order:
    """Меняет статус заказа с проверкой допустимого перехода."""
    allowed = ORDER_TRANSITIONS.get(order.status, set())
    if new_status not in allowed:
        raise OrderError(
            f"Недопустимый переход статуса: {order.status} → {new_status}"
        )

    async with transaction(db):
        await orders_repo.update_status(db, order, new_status, commit=False)
        if notify:
            await _notify_client(
                db,
                order,
                title="Статус заказа обновлён",
                body=f"Ваш заказ: {STATUS_LABELS.get(new_status, new_status)}.",
                kind=NOTIFY_ORDER_STATUS,
            )

    # Сквозная аналитика: выполненный заказ → офлайн-конверсия в Яндекс.Метрику
    # (Директ учится на цели «Клининг выполнен»). После commit, фоном.
    if new_status == ORDER_DONE:
        _schedule_offline_conversion(order.id)

    return order


async def convert_lead_to_order(
    db: AsyncSession,
    lead: Lead,
    *,
    service_type: str,
    rooms: int,
    bathrooms: int,
    addon_codes: list[str] | None = None,
) -> Order:
    """Конверсия лида в заказ (собственная CRM).

    Менеджер выбирает услугу и параметры → пересчитываем цену единой логикой
    quoting → создаём заказ, лид переводим в converted. Дальше заказ живёт
    в канбане «Заказы» (назначение клинера, статусы, финансы).
    """
    if lead.city is None:
        raise OrderError("У лида не указан город — заполните город перед конверсией")

    try:
        bundle = await build_quote(
            db,
            city_slug=lead.city.slug,
            service_type=service_type,
            rooms=rooms,
            bathrooms=bathrooms,
            addon_codes=addon_codes or [],
            promo_code=None,
        )
    except QuotingError as exc:
        raise OrderError(exc.message) from exc

    addons_snapshot = [
        {"code": a.code, "name": a.name, "price": float(a.price), "minutes": a.minutes}
        for a in bundle.addons
    ]
    async with transaction(db):
        order = await booking_repo.create_order(
            db,
            lead_id=lead.id,
            city_id=bundle.city.id,
            service_id=bundle.service.id,
            master_id=None,
            rooms=rooms,
            bathrooms=bathrooms,
            addons=addons_snapshot,
            total_price=Decimal(bundle.result.total),
            est_minutes=bundle.result.est_minutes,
            discount_code=None,
            commit=False,
        )
        await leads_repo.update_lead_card(db, lead, status=LEAD_CONVERTED, commit=False)
    return order


def _schedule_offline_conversion(order_id: uuid.UUID) -> None:
    """Планирует загрузку конверсии: Celery, при недоступности — asyncio-таск."""
    try:
        from app.tasks.analytics import upload_offline_conversion

        upload_offline_conversion.delay(str(order_id))
        return
    except Exception as exc:  # noqa: BLE001 — брокер недоступен (dev без Redis)
        logger.warning("Celery недоступен для офлайн-конверсии, шлём напрямую: %s", exc)

    from app.services.yandex_offline import upload_order_done_conversion

    try:
        asyncio.get_running_loop().create_task(upload_order_done_conversion(order_id))
    except RuntimeError:
        logger.error("Нет event loop для отправки офлайн-конверсии по заказу %s", order_id)


async def assign_master(
    db: AsyncSession, order: Order, master_id: uuid.UUID | None, *, notify: bool = True
) -> Order:
    """Назначает/снимает мастера. При назначении заказ переходит в 'assigned'."""
    async with transaction(db):
        await orders_repo.assign_master(db, order, master_id, commit=False)

        if master_id is not None and order.status == ORDER_NEW:
            await orders_repo.update_status(db, order, ORDER_ASSIGNED, commit=False)

        if notify and master_id is not None:
            # Уведомляем клинера, если у него есть учётная запись.
            assigned = order.master
            if assigned is not None and assigned.user_id is not None:
                await notifications_repo.create_notification(
                    db,
                    user_id=assigned.user_id,
                    title="Новый заказ",
                    body="Вам назначен новый заказ на уборку.",
                    kind=NOTIFY_ORDER_ASSIGNED,
                    data={"order_id": str(order.id)},
                    commit=False,
                )
    return order


async def _notify_client(
    db: AsyncSession, order: Order, *, title: str, body: str, kind: str
) -> None:
    """Создаёт уведомление клиенту заказа (если у него есть учётная запись).

    Часть единицы работы вызывающего сервиса — без собственного commit.
    """
    lead = order.lead
    if lead is None or not lead.phone:
        return
    user = await users_repo.get_user_by_phone(db, lead.phone)
    if user is None:
        return
    await notifications_repo.create_notification(
        db,
        user_id=user.id,
        title=title,
        body=body,
        kind=kind,
        data={"order_id": str(order.id)},
        commit=False,
    )
