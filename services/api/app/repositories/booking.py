"""Доступ к данным мастеров, расписаний и заказов (букинг).

Мутирующие функции принимают `commit`: True (по умолчанию) — самостоятельная
операция; False — часть единицы работы сервиса (`app.core.db.transaction`).
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.catalog import Master, MasterSchedule
from app.models.orders import ORDER_NEW, Order


async def list_masters(db: AsyncSession, city_id: uuid.UUID) -> list[Master]:
    stmt = (
        select(Master)
        .where(Master.city_id == city_id, Master.is_active.is_(True))
        .order_by(Master.rating.desc())
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_available_slots(
    db: AsyncSession,
    *,
    city_id: uuid.UUID,
    on_date: date | None = None,
    master_id: uuid.UUID | None = None,
) -> list[MasterSchedule]:
    """Свободные слоты активных мастеров города (опц. фильтр по дате/мастеру)."""
    stmt = (
        select(MasterSchedule)
        .join(Master, Master.id == MasterSchedule.master_id)
        .where(
            Master.city_id == city_id,
            Master.is_active.is_(True),
            MasterSchedule.is_booked.is_(False),
        )
        .options(selectinload(MasterSchedule.master))
        .order_by(MasterSchedule.work_date, MasterSchedule.start_time)
    )
    if on_date is not None:
        stmt = stmt.where(MasterSchedule.work_date == on_date)
    if master_id is not None:
        stmt = stmt.where(MasterSchedule.master_id == master_id)
    return list((await db.execute(stmt)).scalars().all())


async def get_slot(
    db: AsyncSession, slot_id: uuid.UUID, *, for_update: bool = False
) -> MasterSchedule | None:
    """Слот мастера; for_update=True — блокировка строки (SELECT … FOR UPDATE)
    на время транзакции бронирования, чтобы два клиента не заняли один слот."""
    return await db.get(
        MasterSchedule,
        slot_id,
        options=[selectinload(MasterSchedule.master)],
        with_for_update=for_update,
    )


async def create_order(
    db: AsyncSession,
    *,
    lead_id: uuid.UUID,
    city_id: uuid.UUID,
    service_id: uuid.UUID,
    master_id: uuid.UUID | None,
    rooms: int,
    bathrooms: int,
    addons: list[dict] | None,
    total_price,
    est_minutes: int,
    discount_code: str | None,
    status: str = ORDER_NEW,
    scheduled_at=None,
    commit: bool = True,
) -> Order:
    order = Order(
        lead_id=lead_id,
        city_id=city_id,
        service_id=service_id,
        master_id=master_id,
        rooms=rooms,
        bathrooms=bathrooms,
        addons=addons,
        total_price=total_price,
        est_minutes=est_minutes,
        discount_code=discount_code,
        status=status,
        scheduled_at=scheduled_at,
    )
    db.add(order)
    if commit:
        await db.commit()
    else:
        await db.flush()
    await db.refresh(order)
    return order


async def mark_slot_booked(db: AsyncSession, slot: MasterSchedule, *, commit: bool = True) -> None:
    slot.is_booked = True
    if commit:
        await db.commit()
    else:
        await db.flush()
