"""Доступ к данным каталога (города, услуги, доп.услуги, промокоды).

Слой репозитория отделяет SQL от роутеров и сервисов.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.catalog import AddonService, Branch, City, Service
from app.models.marketing import Promotion


async def get_active_city_by_slug(db: AsyncSession, slug: str) -> City | None:
    stmt = select(City).where(City.slug == slug, City.is_active.is_(True))
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_active_cities(db: AsyncSession) -> list[City]:
    stmt = select(City).where(City.is_active.is_(True)).order_by(City.name)
    return list((await db.execute(stmt)).scalars().all())


async def get_service(db: AsyncSession, city_id, service_type: str) -> Service | None:
    stmt = select(Service).where(
        Service.city_id == city_id,
        Service.type == service_type,
        Service.is_active.is_(True),
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def list_services(db: AsyncSession, city_id) -> list[Service]:
    stmt = select(Service).where(
        Service.city_id == city_id, Service.is_active.is_(True)
    )
    return list((await db.execute(stmt)).scalars().all())


async def list_addons(db: AsyncSession, city_id, codes: list[str] | None = None) -> list[AddonService]:
    stmt = select(AddonService).where(
        AddonService.city_id == city_id, AddonService.is_active.is_(True)
    )
    if codes is not None:
        stmt = stmt.where(AddonService.code.in_(codes))
    return list((await db.execute(stmt)).scalars().all())


async def list_branches(db: AsyncSession, city_id) -> list[Branch]:
    stmt = select(Branch).where(
        Branch.city_id == city_id,
        Branch.is_active.is_(True),
    ).order_by(Branch.name)
    return list((await db.execute(stmt)).scalars().all())


async def get_valid_promo(db: AsyncSession, city_id, code: str) -> Promotion | None:
    """Активный промокод: глобальный (city_id IS NULL) или для конкретного города."""
    now = datetime.now(timezone.utc)
    stmt = select(Promotion).where(
        Promotion.code == code,
        Promotion.is_active.is_(True),
        ((Promotion.city_id == city_id) | (Promotion.city_id.is_(None))),
    )
    promo = (await db.execute(stmt)).scalar_one_or_none()
    if promo is None:
        return None
    if promo.valid_until is not None and promo.valid_until < now:
        return None
    return promo

