"""Интеграционный тест сида мультирегиональных данных (требует PostgreSQL).

Проверяем структуру засеянных данных (города, каталог, филиалы), а не
конкретные телефоны/адреса — контакты меняются бизнесом без правки тестов.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.models.catalog import AddonService, Branch, City, Service
from app.seed import seed

pytestmark = pytest.mark.integration


async def test_seed_creates_tyumen_and_ufa_with_branches(db_session):
    await seed()

    tyumen = (
        await db_session.execute(select(City).where(City.slug == "tyumen"))
    ).scalar_one_or_none()
    ufa = (
        await db_session.execute(select(City).where(City.slug == "ufa"))
    ).scalar_one_or_none()

    assert tyumen is not None
    assert tyumen.name_prepositional == "в Тюмени"
    assert tyumen.phone.startswith("+7")
    assert "@" in tyumen.email
    assert tyumen.is_active is True

    assert ufa is not None
    assert ufa.name_prepositional == "в Уфе"
    assert ufa.phone.startswith("+7")
    assert "@" in ufa.email
    assert ufa.is_active is True

    for city in (tyumen, ufa):
        services = (
            await db_session.execute(select(Service).where(Service.city_id == city.id))
        ).scalars().all()
        assert {s.type for s in services} >= {"maintenance", "general", "post_renovation", "office"}
        # Офисный тариф — «от м²», жилые — по комнатам.
        office = next(s for s in services if s.type == "office")
        assert float(office.price_per_sqm) > 0

        addons = (
            await db_session.execute(select(AddonService).where(AddonService.city_id == city.id))
        ).scalars().all()
        assert len(addons) >= 4
        windows = next(a for a in addons if a.code == "windows")
        assert windows.unit and windows.max_qty > 1

    tyumen_branch_names = {
        branch.name
        for branch in (
            await db_session.execute(select(Branch).where(Branch.city_id == tyumen.id))
        ).scalars().all()
    }
    ufa_branch_names = {
        branch.name
        for branch in (
            await db_session.execute(select(Branch).where(Branch.city_id == ufa.id))
        ).scalars().all()
    }

    assert "Точка Чистоты — Центр" in tyumen_branch_names
    assert "Точка Чистоты — Восточный" in tyumen_branch_names
    assert "Точка Чистоты — Проспект Октября" in ufa_branch_names
    assert "Точка Чистоты — Сипайлово" in ufa_branch_names


async def test_seed_is_idempotent(db_session):
    await seed()
    await seed()

    cities = (await db_session.execute(select(City))).scalars().all()
    assert len([c for c in cities if c.slug in ("tyumen", "ufa")]) == 2
    for city in cities:
        services = (
            await db_session.execute(select(Service).where(Service.city_id == city.id))
        ).scalars().all()
        assert len({s.type for s in services}) == len(services)
