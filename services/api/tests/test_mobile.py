"""Тесты мобильного API (Этап 4), не требующие БД.

Проверяем регистрацию маршрутов и обязательную авторизацию (RBAC-гейт
срабатывает до обращения к базе, поэтому Postgres не нужен).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_mobile_routes_registered():
    # OpenAPI — канонический источник зарегистрированных маршрутов.
    paths = app.openapi()["paths"]
    assert "get" in paths["/api/v1/mobile/orders"]
    assert "get" in paths["/api/v1/mobile/orders/{order_id}"]
    assert "patch" in paths["/api/v1/mobile/orders/{order_id}/status"]
    assert "get" in paths["/api/v1/mobile/profile"]
    assert "get" in paths["/api/v1/mobile/notifications"]
    assert "post" in paths["/api/v1/mobile/notifications/{notification_id}/read"]
    assert "post" in paths["/api/v1/mobile/push-tokens"]


def test_mobile_orders_requires_auth():
    assert client.get("/api/v1/mobile/orders").status_code == 401


def test_mobile_profile_requires_auth():
    assert client.get("/api/v1/mobile/profile").status_code == 401


def test_mobile_status_change_requires_auth():
    response = client.patch(
        "/api/v1/mobile/orders/00000000-0000-0000-0000-000000000000/status",
        json={"status": "in_progress"},
    )
    assert response.status_code == 401


def test_mobile_invalid_token_rejected():
    response = client.get(
        "/api/v1/mobile/profile", headers={"Authorization": "Bearer not-a-jwt"}
    )
    assert response.status_code == 401
