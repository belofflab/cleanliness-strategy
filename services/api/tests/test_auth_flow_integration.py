"""Интеграционный поток аутентификации: OTP → access/refresh → ротация → logout.

Требует PostgreSQL (пропускается без DATABASE_URL на живую БД). SMS работает
в mock-режиме (SMS_ENABLED=false), поэтому код приходит в `debug_code`.

TestClient используется как контекстный менеджер: так все запросы теста
выполняются в одном event loop и пул соединений БД не пересекает loop'ы.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.db import engine
from app.core.rate_limit import MemoryBackend, rate_limiter
from app.main import app
from app.models.catalog import City
from app.repositories import masters as masters_repo
from app.seed import seed

pytestmark = pytest.mark.integration


def _request_code(client: TestClient, phone: str, role: str = "client") -> str:
    response = client.post("/api/v1/auth/otp/request", json={"phone": phone, "role": role})
    assert response.status_code == 200, response.text
    code = response.json()["debug_code"]
    assert code and len(code) == 4
    return code


def _login(client: TestClient, phone: str, role: str = "client") -> dict:
    code = _request_code(client, phone, role)
    verified = client.post(
        "/api/v1/auth/otp/verify", json={"phone": phone, "code": code, "role": role}
    )
    assert verified.status_code == 200, verified.text
    return verified.json()


def _auth(pair: dict) -> dict:
    return {"Authorization": f"Bearer {pair['access_token']}"}


async def test_otp_login_and_refresh_rotation_with_reuse_detection(db_session):
    await engine.dispose(close=False)
    phone = "+7 (999) 111-22-33"  # формат с сайта/мобайла — сервер нормализует

    with TestClient(app) as client:
        code = _request_code(client, phone)

        wrong_code = "0000" if code != "0000" else "1111"
        wrong = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": wrong_code})
        assert wrong.status_code == 400

        verified = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code})
        assert verified.status_code == 200, verified.text
        pair = verified.json()
        assert pair["token_type"] == "bearer"

        me = client.get("/api/v1/auth/me", headers=_auth(pair))
        assert me.status_code == 200
        assert me.json()["phone"] == "+79991112233"
        assert me.json()["role"] == "client"

        # Код одноразовый.
        reused = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code})
        assert reused.status_code == 400

        refreshed = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
        assert refreshed.status_code == 200, refreshed.text
        new_pair = refreshed.json()
        assert new_pair["refresh_token"] != pair["refresh_token"]

        # Ротация: старый refresh отозван.
        stale = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
        assert stale.status_code == 401

        # Повторное использование отозванного токена = кража: вся семья отозвана,
        # новый refresh тоже недействителен.
        killed = client.post("/api/v1/auth/refresh", json={"refresh_token": new_pair["refresh_token"]})
        assert killed.status_code == 401

        # Текущее поведение: access-токен stateless и живёт до истечения TTL.
        assert client.get("/api/v1/auth/me", headers=_auth(new_pair)).status_code == 200


async def test_logout_revokes_device_tokens(db_session):
    await engine.dispose(close=False)
    phone = "+7 (999) 111-22-55"

    with TestClient(app) as client:
        pair = _login(client, phone)
        rotated = client.post("/api/v1/auth/refresh", json={"refresh_token": pair["refresh_token"]})
        assert rotated.status_code == 200
        current = rotated.json()

        logged_out = client.post("/api/v1/auth/logout", json={"refresh_token": current["refresh_token"]})
        assert logged_out.status_code == 204
        after_logout = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": current["refresh_token"]}
        )
        assert after_logout.status_code == 401

        # Новый вход после logout работает.
        assert _login(client, phone)["access_token"]


async def test_master_role_requires_master_card(db_session):
    await seed()
    ufa = (await db_session.execute(select(City).where(City.slug == "ufa"))).scalar_one()
    phone_no_card = "+7 (999) 222-33-44"
    phone_with_card = "+7 (999) 222-33-55"
    master = await masters_repo.get_master_by_phone(db_session, "+79992223355")
    if master is None:
        master = await masters_repo.create_master(
            db_session,
            city_id=ufa.id,
            full_name="Интеграционный клинер",
            phone="+79992223355",
            photo_url=None,
        )
    await engine.dispose(close=False)

    with TestClient(app) as client:
        # Самозапись клинером невозможна: без карточки мастера код не отправляется.
        denied = client.post(
            "/api/v1/auth/otp/request", json={"phone": phone_no_card, "role": "master"}
        )
        assert denied.status_code == 400
        assert "менеджер" in denied.json()["detail"]

        # Клиент остаётся клиентом, даже если просит роль master.
        client_pair = _login(client, phone_no_card, role="client")
        assert client.get("/api/v1/auth/me", headers=_auth(client_pair)).json()["role"] == "client"

        # По карточке мастера, заведённой менеджером, вход клинера работает
        # и учётка связывается с карточкой.
        master_pair = _login(client, phone_with_card, role="master")
        profile = client.get("/api/v1/mobile/profile", headers=_auth(master_pair))
        assert profile.status_code == 200, profile.text
        assert profile.json()["role"] == "master"
        assert profile.json()["master"]["full_name"] == master.full_name


async def test_otp_request_is_rate_limited_per_phone(db_session, monkeypatch):
    await engine.dispose(close=False)
    monkeypatch.setattr(rate_limiter, "backend", MemoryBackend())
    phone = "+7 (999) 333-44-55"

    with TestClient(app) as client:
        for _ in range(3):
            assert client.post("/api/v1/auth/otp/request", json={"phone": phone}).status_code == 200
        blocked = client.post("/api/v1/auth/otp/request", json={"phone": phone})

    assert blocked.status_code == 429
    assert blocked.headers["Retry-After"]
    assert blocked.json()["error"]["code"] == "rate_limited"
