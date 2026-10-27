"""Доступ к данным заказов (мобайл клинера/клиента и админ-CRM).

Мутирующие функции принимают `commit`: True (по умолчанию) — самостоятельная
операция; False — часть единицы работы сервиса (`app.core.db.transaction`),
тогда выполняется только flush.
"""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Master
from app.models.orders import Lead, Order

__all__ = [
    "assign_master",
    "get_master_by_user_id",
    "get_order",
    "link_master_by_phone",
    "list_for_board",
    "list_orders",
    "list_orders_for_master",
    "list_orders_for_phone",
    "update_status",
]

# Связи, которые нужны для сериализации заказа (избегаем ленивой загрузки в async).
_ORDER_LOADS = (selectinload(Order.lead),)


async def _persist(db: AsyncSession, obj, *, commit: bool) -> None:
    if commit:
        await db.commit()
    else:
        await db.flush()
    await db.refresh(obj)


async def get_order(db: AsyncSession, order_id: uuid.UUID) -> Order | None:
    return await db.get(Order, order_id, options=list(_ORDER_LOADS))


async def get_master_by_user_id(db: AsyncSession, user_id: uuid.UUID) -> Master | None:
    stmt = select(Master).where(Master.user_id == user_id)
    return (await db.execute(stmt)).scalar_one_or_none()


async def link_master_by_phone(
    db: AsyncSession, phone: str, user_id: uuid.UUID, *, commit: bool = True
) -> Master | None:
    """Привязывает учётку клинера к карточке мастера с таким телефоном.

    Вызывается при OTP-входе мастера: если в городе заведён мастер с этим
    телефоном и без привязки — связываем, и его заказы становятся видны в мобайле.
    """
    existing = await get_master_by_user_id(db, user_id)
    if existing is not None:
        return existing

    stmt = select(Master).where(Master.phone == phone, Master.user_id.is_(None))
    master = (await db.execute(stmt)).scalar_one_or_none()
    if master is not None:
        master.user_id = user_id
        await _persist(db, master, commit=commit)
    return master


async def list_orders_for_master(
    db: AsyncSession, master_id: uuid.UUID, *, statuses: list[str] | None = None
) -> list[Order]:
    stmt = (
        select(Order)
        .where(Order.master_id == master_id)
        .options(*_ORDER_LOADS)
        .order_by(Order.scheduled_at.is_(None), Order.scheduled_at, Order.created_at.desc())
    )
    if statuses:
        stmt = stmt.where(Order.status.in_(statuses))
    return list((await db.execute(stmt)).scalars().all())


async def list_orders_for_phone(
    db: AsyncSession, phone: str, *, statuses: list[str] | None = None
) -> list[Order]:
    """Заказы клиента — по телефону лида (покрывает и веб-, и app-заявки)."""
    stmt = (
        select(Order)
        .join(Lead, Lead.id == Order.lead_id)
        .where(Lead.phone == phone)
        .options(*_ORDER_LOADS)
        .order_by(Order.created_at.desc())
    )
    if statuses:
        stmt = stmt.where(Order.status.in_(statuses))
    return list((await db.execute(stmt)).scalars().all())


async def list_orders(
    db: AsyncSession,
    *,
    city_id: uuid.UUID | None = None,
    status: str | None = None,
    master_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Order], int]:
    """Список заказов для админки с фильтрами и пагинацией.

    Возвращает (страница, всего). Фильтр по city_id — основа регионального
    разграничения данных в CRM-панели.
    """
    filters = []
    if city_id is not None:
        filters.append(Order.city_id == city_id)
    if status is not None:
        filters.append(Order.status == status)
    if master_id is not None:
        filters.append(Order.master_id == master_id)

    base = select(Order).where(*filters)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()

    stmt = (
        base.options(*_ORDER_LOADS)
        .order_by(Order.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = list((await db.execute(stmt)).scalars().all())
    return rows, total


async def list_for_board(
    db: AsyncSession, *, city_id: uuid.UUID | None = None, limit: int = 500
) -> list[Order]:
    """Заказы для канбана (без пагинации, с разумным потолком).

    Группировку по статусам делает вызывающий код — так одним запросом
    наполняем все колонки доски.
    """
    stmt = select(Order)
    if city_id is not None:
        stmt = stmt.where(Order.city_id == city_id)
    stmt = stmt.options(*_ORDER_LOADS).order_by(Order.created_at.desc()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def update_status(
    db: AsyncSession, order: Order, status: str, *, commit: bool = True
) -> Order:
    order.status = status
    await _persist(db, order, commit=commit)
    return order


async def assign_master(
    db: AsyncSession, order: Order, master_id: uuid.UUID | None, *, commit: bool = True
) -> Order:
    order.master_id = master_id
    # refresh() перечитывает и связь order.master (lazy="selectin") под новый FK.
    await _persist(db, order, commit=commit)
    return order
