"""Интеграционные проверки city-aware контент-эндпоинта (требует PostgreSQL).

Ожидаемые значения берутся из настроек (DEFAULT_CITY_SLUG, PUBLIC_BASE_DOMAIN)
и из засеянных данных города, а не зашиваются в тест.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.db import engine
from app.main import app
from app.models.catalog import City
from app.seed import seed

pytestmark = pytest.mark.integration


def _origin(slug: str) -> str:
    settings = get_settings()
    if slug == settings.default_city_slug:
        return f"https://{settings.public_base_domain}"
    return f"https://{slug}.{settings.public_base_domain}"


async def _city(db, slug: str) -> City:
    return (await db.execute(select(City).where(City.slug == slug))).scalar_one()


async def test_content_city_from_host_subdomain(db_session):
    await seed()
    ufa = await _city(db_session, "ufa")
    await engine.dispose(close=False)
    base = get_settings().public_base_domain

    client = TestClient(app)
    resp = client.get("/api/v1/content", headers={"host": f"ufa.{base}"})

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["city"]["slug"] == "ufa"
    assert body["city"]["phone"] == ufa.phone
    assert body["seo"]["canonical"].startswith(_origin("ufa"))
    assert body["seo"]["hreflang"]["x-default"].startswith(_origin(get_settings().default_city_slug))
    assert len(body["services"]) >= 3
    assert len(body["branches"]) >= 1


async def test_content_city_from_header_when_apex_host(db_session):
    await seed()
    tyumen = await _city(db_session, "tyumen")
    await engine.dispose(close=False)
    base = get_settings().public_base_domain

    client = TestClient(app)
    resp = client.get(
        "/api/v1/content",
        headers={"host": base, "x-city-slug": "tyumen"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["city"]["slug"] == "tyumen"
    assert body["city"]["phone"] == tyumen.phone
    assert body["seo"]["canonical"].startswith(_origin("tyumen"))


async def test_content_unknown_subdomain_falls_back_to_default_city(db_session):
    await seed()
    await engine.dispose(close=False)
    base = get_settings().public_base_domain

    client = TestClient(app)
    resp = client.get("/api/v1/content", headers={"host": f"foo.{base}"})

    assert resp.status_code == 200, resp.text
    assert resp.json()["city"]["slug"] == get_settings().default_city_slug


async def test_content_service_subdomains_are_not_cities(db_session):
    await seed()
    await engine.dispose(close=False)
    base = get_settings().public_base_domain

    # Несколько запросов в одном тесте — TestClient как контекстный менеджер
    # (один event loop на все запросы, пул соединений БД не пересекает loop'ы).
    with TestClient(app) as client:
        for host in (f"api.{base}", f"www.{base}", base):
            resp = client.get("/api/v1/content", headers={"host": host})
            assert resp.status_code == 200, host
            assert resp.json()["city"]["slug"] == get_settings().default_city_slug, host


async def test_content_unknown_header_city_returns_404(db_session):
    await seed()
    await engine.dispose(close=False)
    base = get_settings().public_base_domain

    client = TestClient(app)
    resp = client.get(
        "/api/v1/content",
        headers={"host": base, "x-city-slug": "unknown"},
    )

    assert resp.status_code == 404
