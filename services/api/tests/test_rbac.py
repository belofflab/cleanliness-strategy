"""Ролевые гейты (RBAC) без БД.

`get_current_user` подменяется фейковым пользователем нужной роли через
`app.dependency_overrides`, поэтому проверяется именно слой авторизации:
403 для не-staff на /admin/*, ограничения клинера/клиента на /mobile/*,
запрет менеджеру выдавать привилегированные роли.
"""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.auth_deps import get_current_user, require_roles
from app.main import app
from app.models.auth import ROLE_ADMIN, ROLE_CLIENT, ROLE_MANAGER, ROLE_MASTER, User


def _fake_user(role: str) -> User:
    return User(id=uuid.uuid4(), phone="+79990000000", role=role, is_active=True)


@pytest.fixture
def client_as():
    """Фабрика TestClient, в котором текущий пользователь имеет заданную роль."""

    def _factory(role: str) -> TestClient:
        app.dependency_overrides[get_current_user] = lambda: _fake_user(role)
        return TestClient(app)

    yield _factory
    app.dependency_overrides.pop(get_current_user, None)


# (метод, путь, тело) — staff-эндпоинты, закрытые для client/master.
ADMIN_ROUTES = [
    ("GET", "/api/v1/admin/orders", None),
    ("GET", "/api/v1/admin/orders/board", None),
    ("GET", "/api/v1/admin/leads", None),
    ("GET", "/api/v1/admin/leads/summary", None),
    ("GET", "/api/v1/admin/users", None),
    ("GET", "/api/v1/admin/masters", None),
    ("GET", "/api/v1/admin/finance", None),
    ("GET", "/api/v1/admin/finance/summary", None),
    ("POST", "/api/v1/admin/reviews/sync", None),
    ("POST", "/api/v1/admin/media/presign", {"filename": "photo.jpg", "owner_type": "other"}),
]


@pytest.mark.parametrize("role", [ROLE_CLIENT, ROLE_MASTER])
@pytest.mark.parametrize("method,path,body", ADMIN_ROUTES)
def test_admin_routes_forbidden_for_non_staff(client_as, role, method, path, body):
    response = client_as(role).request(method, path, json=body)
    assert response.status_code == 403, f"{role} {method} {path}: {response.text}"


def test_admin_routes_require_token():
    # Без токена — 401 ещё до RBAC (страховка на случай смены auth-зависимости).
    for method, path, body in ADMIN_ROUTES:
        response = TestClient(app).request(method, path, json=body)
        assert response.status_code == 401, f"{method} {path}"


@pytest.mark.parametrize("role", [ROLE_MANAGER, ROLE_ADMIN])
async def test_require_roles_lets_staff_through(role):
    checker = require_roles(ROLE_MANAGER, ROLE_ADMIN)
    user = await checker(user=_fake_user(role))
    assert user.role == role


@pytest.mark.parametrize("role", [ROLE_CLIENT, ROLE_MASTER])
async def test_require_roles_rejects_other_roles(role):
    checker = require_roles(ROLE_MANAGER, ROLE_ADMIN)
    with pytest.raises(HTTPException) as exc_info:
        await checker(user=_fake_user(role))
    assert exc_info.value.status_code == 403


def test_manager_cannot_grant_privileged_roles(client_as):
    # Роли manager/admin выдаёт только администратор — проверка идёт до обращения к БД.
    for target_role in (ROLE_MANAGER, ROLE_ADMIN):
        response = client_as(ROLE_MANAGER).post(
            "/api/v1/admin/users",
            json={"phone": "+79990000001", "role": target_role, "password": "secret123"},
        )
        assert response.status_code == 403, target_role


def test_client_cannot_change_order_status(client_as):
    response = client_as(ROLE_CLIENT).patch(
        f"/api/v1/mobile/orders/{uuid.uuid4()}/status", json={"status": "in_progress"}
    )
    assert response.status_code == 403


@pytest.mark.parametrize("status", ["cancelled", "assigned", "new"])
def test_master_cannot_set_statuses_outside_allowed_targets(client_as, status):
    # Валидация целевого статуса выполняется до загрузки заказа из БД.
    response = client_as(ROLE_MASTER).patch(
        f"/api/v1/mobile/orders/{uuid.uuid4()}/status", json={"status": status}
    )
    assert response.status_code == 400
