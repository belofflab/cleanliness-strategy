"""Интеграционный поток букинга и приёма лидов (требует PostgreSQL).

Покрывает дефект R1 аудита (телефон лида нормализуется → клиент видит свои
заказы в `/mobile/orders`) и атомарность бронирования: лид, заказ и бронь
слота либо записываются вместе, либо не записываются вовсе.

TestClient используется как контекстный менеджер: все запросы теста идут в
одном event loop, и пул соединений БД не пересекает loop'ы.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.core.config import get_settings
from app.core.db import engine
from app.main import app
from app.models.orders import Lead
from app.repositories import leads as leads_repo
from app.seed import seed

pytestmark = pytest.mark.integration


def _login(client: TestClient, phone: str) -> dict:
    code = client.post("/api/v1/auth/otp/request", json={"phone": phone}).json()["debug_code"]
    pair = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code}).json()
    return {"Authorization": f"Bearer {pair['access_token']}"}


async def _free_all_slots(db_session) -> None:
    """Локальная БД переживает прогоны: освобождаем слоты, чтобы букинг всегда был возможен."""
    await db_session.execute(text("UPDATE master_schedules SET is_booked = false"))
    await db_session.commit()


def _booking_payload(phone: str, slot_id: str | None = None) -> dict:
    return {
        "name": "Интеграционный клиент",
        "phone": phone,
        "city_slug": "ufa",
        "service_type": "general",
        "rooms": 2,
        "bathrooms": 1,
        "addon_codes": ["windows"],
        "promo_code": "CLEAN10",
        "schedule_id": slot_id,
        "source": "mobile",
    }


async def test_booking_books_slot_and_client_sees_order(db_session):
    await seed()
    await _free_all_slots(db_session)
    await engine.dispose(close=False)
    phone = "+7 (999) 555-66-77"

    with TestClient(app) as client:
        slots = client.get("/api/v1/booking/availability", params={"city_slug": "ufa"}).json()
        assert slots, "сид должен создавать свободные слоты мастеров"
        slot = slots[0]

        booked = client.post("/api/v1/booking/bookings", json=_booking_payload(phone, slot["id"]))
        assert booked.status_code == 201, booked.text
        body = booked.json()
        assert body["city"] == "Уфа"
        assert body["master_name"] == slot["master_name"]
        assert body["total"] > 0

        # Слот занят и больше не отдаётся как свободный; повторная бронь невозможна.
        remaining = client.get(
            "/api/v1/booking/availability", params={"city_slug": "ufa"}
        ).json()
        assert slot["id"] not in {s["id"] for s in remaining}
        again = client.post("/api/v1/booking/bookings", json=_booking_payload(phone, slot["id"]))
        assert again.status_code == 400
        assert again.json()["detail"] == "Выбранный слот недоступен"
        assert again.json()["error"]["code"] == "http_400"

        # Клиент с тем же номером (в другом формате) видит заказ в мобайле.
        headers = _login(client, "8 999 555 66 77")
        my_orders = client.get(
            "/api/v1/mobile/orders", params={"scope": "active"}, headers=headers
        )
        assert my_orders.status_code == 200, my_orders.text
        assert body["order_id"] in {o["id"] for o in my_orders.json()}

        order = client.get(f"/api/v1/mobile/orders/{body['order_id']}", headers=headers).json()
        assert order["status"] == "assigned"
        assert order["customer_phone"] == "+79995556677"
        assert order["master_name"] == slot["master_name"]


async def test_booking_is_atomic_on_failure(db_session, monkeypatch):
    """Сбой после создания лида откатывает и лид, и бронь слота (единица работы)."""
    await seed()
    await _free_all_slots(db_session)
    await db_session.execute(text("SELECT 1"))  # соединение сессии закреплено за текущим loop
    await engine.dispose(close=False)
    phone = "+7 (999) 555-66-79"

    async def explode(*args, **kwargs):
        raise RuntimeError("db exploded after lead insert")

    monkeypatch.setattr("app.services.booking.booking_repo.create_order", explode)

    with TestClient(app, raise_server_exceptions=False) as client:
        slot = client.get("/api/v1/booking/availability", params={"city_slug": "ufa"}).json()[0]
        failed = client.post("/api/v1/booking/bookings", json=_booking_payload(phone, slot["id"]))
        assert failed.status_code == 500
        assert failed.json()["error"]["code"] == "internal_error"
        assert "exploded" not in failed.text

        # Слот остался свободным.
        remaining = client.get(
            "/api/v1/booking/availability", params={"city_slug": "ufa"}
        ).json()
        assert slot["id"] in {s["id"] for s in remaining}

    # Лид не сохранился.
    orphan = (
        await db_session.execute(select(Lead).where(Lead.phone == "+79995556679"))
    ).scalars().all()
    assert orphan == []


async def test_lead_from_site_is_normalized_and_gets_default_city(db_session):
    await seed()
    # Закрепляем соединение сессии за текущим event loop до запуска TestClient.
    await db_session.execute(text("SELECT 1"))
    await engine.dispose(close=False)

    with TestClient(app) as client:
        created = client.post(
            "/api/v1/leads",
            json={"name": "Веб-заявка", "phone": "8 (999) 777-88-99", "source": "quiz"},
        )
    assert created.status_code == 201, created.text
    assert created.json()["status"] == "new"

    lead = await leads_repo.get_lead(db_session, uuid.UUID(created.json()["id"]))
    assert lead is not None
    assert lead.phone == "+79997778899"
    assert lead.city is not None
    assert lead.city.slug == get_settings().default_city_slug


async def test_booking_without_city_uses_default_city(db_session):
    await seed()
    await engine.dispose(close=False)

    with TestClient(app) as client:
        booked = client.post(
            "/api/v1/booking/bookings",
            json={
                "name": "Без города",
                "phone": "+7 999 555 66 78",
                "service_type": "maintenance",
                "rooms": 1,
                "bathrooms": 1,
                "addon_codes": [],
            },
        )
    assert booked.status_code == 201, booked.text
    default_slug = get_settings().default_city_slug
    expected_city = {"ufa": "Уфа", "tyumen": "Тюмень"}[default_slug]
    assert booked.json()["city"] == expected_city
