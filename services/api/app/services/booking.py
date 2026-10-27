"""Оркестрация бронирования.

Одна единица работы (`app.core.db.transaction`):
1. Считаем стоимость через общий сервис quoting (та же логика, что и калькулятор).
2. Блокируем выбранный слот мастера (SELECT … FOR UPDATE) и проверяем: свободен,
   принадлежит городу — второй параллельный клиент дождётся блокировки и получит
   «слот недоступен».
3. Сохраняем лид (источник booking) и заказ-снимок выбранных параметров.
4. Помечаем слот занятым.
Всё коммитится разом; при ошибке ничего не остаётся (ни лида без заказа, ни
заказа без брони). Уведомление операторов планирует роутер (BackgroundTasks).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import transaction
from app.core.errors import DomainError
from app.models.catalog import MasterSchedule
from app.models.orders import ORDER_ASSIGNED, ORDER_NEW
from app.modules.pricing.engine import human_minutes
from app.modules.pricing.quoting import QuoteBundle, QuotingError, build_quote
from app.repositories import booking as booking_repo
from app.repositories import leads as leads_repo


class BookingError(DomainError):
    status_code = 400
    code = "booking_error"


def _build_context(bundle: QuoteBundle, rooms: int, bathrooms: int) -> str:
    """Человекочитаемое описание заказа для CRM и менеджера."""
    addons = ", ".join(a.name for a in bundle.addons) or "без доп.услуг"
    return (
        f"{bundle.service.name}: {rooms} комн., {bathrooms} с/у; "
        f"доп: {addons}; итого {bundle.result.total} ₽, "
        f"~{human_minutes(bundle.result.est_minutes)}"
    )


async def create_booking(
    db: AsyncSession,
    *,
    name: str,
    phone: str,
    city_slug: str,
    service_type: str,
    rooms: int,
    bathrooms: int,
    addon_codes: list[str],
    promo_code: str | None,
    schedule_id: str | None,
    source: str,
):
    slot_uuid: uuid.UUID | None = None
    if schedule_id:
        try:
            slot_uuid = uuid.UUID(schedule_id)
        except ValueError as exc:
            raise BookingError("Некорректный идентификатор слота") from exc

    async with transaction(db):
        # 1. Расчёт стоимости (единая логика с калькулятором).
        try:
            bundle = await build_quote(
                db,
                city_slug=city_slug,
                service_type=service_type,
                rooms=rooms,
                bathrooms=bathrooms,
                addon_codes=addon_codes,
                promo_code=promo_code,
            )
        except QuotingError as exc:
            raise BookingError(exc.message) from exc

        # 2. Проверка слота под блокировкой строки (если выбран конкретный мастер/время).
        slot: MasterSchedule | None = None
        master_id: uuid.UUID | None = None
        if slot_uuid is not None:
            slot = await booking_repo.get_slot(db, slot_uuid, for_update=True)
            if slot is None or slot.is_booked:
                raise BookingError("Выбранный слот недоступен")
            if slot.master.city_id != bundle.city.id:
                raise BookingError("Слот относится к другому городу")
            master_id = slot.master_id

        # 3. Лид (заявка фиксируется всегда) — в той же транзакции.
        lead = await leads_repo.create_lead(
            db,
            name=name,
            phone=phone,
            source=source,
            context=_build_context(bundle, rooms, bathrooms),
            utm=None,
            yclid=None,
            ym_uid=None,
            city_id=bundle.city.id,
            commit=False,
        )

        # Снимок доп.услуг в заказ.
        addons_snapshot = [
            {"code": a.code, "name": a.name, "price": float(a.price), "minutes": a.minutes}
            for a in bundle.addons
        ]

        # Если выбран слот — заказ сразу запланирован на конкретного мастера/время.
        scheduled_at: datetime | None = None
        status = ORDER_NEW
        if slot is not None:
            scheduled_at = datetime.combine(
                slot.work_date, slot.start_time, tzinfo=ZoneInfo(bundle.city.timezone)
            )
            status = ORDER_ASSIGNED

        # 4. Заказ.
        order = await booking_repo.create_order(
            db,
            lead_id=lead.id,
            city_id=bundle.city.id,
            service_id=bundle.service.id,
            master_id=master_id,
            rooms=rooms,
            bathrooms=bathrooms,
            addons=addons_snapshot,
            total_price=Decimal(bundle.result.total),
            est_minutes=bundle.result.est_minutes,
            discount_code=bundle.promo_code,
            status=status,
            scheduled_at=scheduled_at,
            commit=False,
        )

        # 5. Бронь слота.
        if slot is not None:
            await booking_repo.mark_slot_booked(db, slot, commit=False)

    return lead, order, bundle, slot
