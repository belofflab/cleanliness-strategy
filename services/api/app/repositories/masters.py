"""Доступ к карточкам мастеров (клинеров) — админ-CRM."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import Master


async def list_masters(
    db: AsyncSession, *, city_id: uuid.UUID | None = None, active_only: bool = False
) -> list[Master]:
    stmt = select(Master)
    if city_id is not None:
        stmt = stmt.where(Master.city_id == city_id)
    if active_only:
        stmt = stmt.where(Master.is_active.is_(True))
    stmt = stmt.order_by(Master.full_name)
    return list((await db.execute(stmt)).scalars().all())


async def get_master(db: AsyncSession, master_id: uuid.UUID) -> Master | None:
    return await db.get(Master, master_id)


async def get_master_by_phone(db: AsyncSession, phone: str) -> Master | None:
    """Карточка мастера по нормализованному телефону — гейт роли клинера при OTP-входе."""
    stmt = select(Master).where(Master.phone == phone).order_by(Master.created_at.desc()).limit(1)
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_master(
    db: AsyncSession,
    *,
    city_id: uuid.UUID,
    full_name: str,
    phone: str | None,
    photo_url: str | None,
) -> Master:
    master = Master(
        city_id=city_id, full_name=full_name, phone=phone, photo_url=photo_url
    )
    db.add(master)
    await db.commit()
    await db.refresh(master)
    return master


async def update_master(db: AsyncSession, master: Master, **fields) -> Master:
    for key, value in fields.items():
        if value is not None and hasattr(master, key):
            setattr(master, key, value)
    await db.commit()
    await db.refresh(master)
    return master
