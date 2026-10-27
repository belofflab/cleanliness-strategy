"""Тесты админ-CRM API (Этап 2), не требующие БД.

Проверяем регистрацию маршрутов и обязательный staff-гейт (manager/admin):
без токена — 401 (срабатывает до обращения к базе).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_admin_routes_registered():
    paths = app.openapi()["paths"]
    assert "get" in paths["/api/v1/admin/orders"]
    assert "get" in paths["/api/v1/admin/orders/board"]
    assert "patch" in paths["/api/v1/admin/orders/{order_id}/status"]
    assert "patch" in paths["/api/v1/admin/orders/{order_id}/assign"]
    assert "get" in paths["/api/v1/admin/leads"]
    assert "get" in paths["/api/v1/admin/users"]
    assert "post" in paths["/api/v1/admin/users"]
    assert "get" in paths["/api/v1/admin/masters"]
    assert "post" in paths["/api/v1/admin/masters"]
    assert "get" in paths["/api/v1/admin/finance"]
    assert "get" in paths["/api/v1/admin/finance/summary"]
    assert "post" in paths["/api/v1/admin/finance"]


def test_admin_orders_requires_auth():
    assert client.get("/api/v1/admin/orders").status_code == 401


def test_admin_users_requires_auth():
    assert client.get("/api/v1/admin/users").status_code == 401


def test_admin_finance_requires_auth():
    assert client.get("/api/v1/admin/finance").status_code == 401


def test_admin_create_user_requires_auth():
    response = client.post(
        "/api/v1/admin/users",
        json={"phone": "+79170000000", "role": "manager", "password": "secret123"},
    )
    assert response.status_code == 401
