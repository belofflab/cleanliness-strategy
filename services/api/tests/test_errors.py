"""Единый формат ошибок API: доменные, HTTP, валидация, необработанные."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

from app.core.errors import DomainError, install_exception_handlers
from app.main import app as real_app


class TeapotError(DomainError):
    status_code = 418
    code = "teapot"


class Payload(BaseModel):
    phone: str = Field(min_length=5)
    rooms: int = Field(ge=0)


def _make_app() -> FastAPI:
    app = FastAPI()
    install_exception_handlers(app)

    @app.get("/domain")
    async def domain():
        raise TeapotError("Я чайник", details=[{"loc": ["cup"], "msg": "пусто"}])

    @app.get("/domain-headers")
    async def domain_headers():
        raise DomainError("Позже", code="later", status_code=429, headers={"Retry-After": "7"})

    @app.get("/http")
    async def http():
        raise HTTPException(status_code=404, detail="Не найдено")

    @app.post("/validate")
    async def validate(payload: Payload):
        return {"ok": True}

    @app.get("/boom")
    async def boom():
        raise RuntimeError("secret internals: db password")

    return app


def test_domain_error_envelope():
    with TestClient(_make_app()) as client:
        response = client.get("/domain")
    assert response.status_code == 418
    body = response.json()
    assert body["detail"] == "Я чайник"  # совместимость со старыми клиентами
    assert body["error"]["code"] == "teapot"
    assert body["error"]["message"] == "Я чайник"
    assert body["error"]["fields"] == [{"loc": ["cup"], "msg": "пусто"}]


def test_domain_error_passes_status_and_headers():
    with TestClient(_make_app()) as client:
        response = client.get("/domain-headers")
    assert response.status_code == 429
    assert response.headers["Retry-After"] == "7"
    assert response.json()["error"]["code"] == "later"


def test_http_exception_keeps_detail_and_adds_code():
    with TestClient(_make_app()) as client:
        response = client.get("/http")
    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Не найдено"
    assert body["error"] == {"code": "http_404", "message": "Не найдено"}


def test_validation_error_is_human_readable_with_fields():
    with TestClient(_make_app()) as client:
        response = client.post("/validate", json={"phone": "1", "rooms": -1})
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body["detail"], str)
    assert body["detail"].startswith("Некорректные данные запроса: phone:")
    assert body["error"]["code"] == "validation_error"
    locs = [field["loc"] for field in body["error"]["fields"]]
    assert ["body", "phone"] in locs
    assert ["body", "rooms"] in locs
    # Введённые значения не возвращаются (могут содержать телефон/пароль).
    assert "input" not in body["error"]["fields"][0]


def test_unhandled_exception_hides_internals():
    with TestClient(_make_app(), raise_server_exceptions=False) as client:
        response = client.get("/boom")
    assert response.status_code == 500
    body = response.json()
    assert body["detail"] == "Внутренняя ошибка сервера"
    assert body["error"]["code"] == "internal_error"
    assert "secret internals" not in response.text


def test_real_app_401_uses_envelope_and_request_id():
    with TestClient(real_app) as client:
        response = client.get("/api/v1/admin/orders", headers={"X-Request-ID": "trace-err-1"})
    assert response.status_code == 401
    body = response.json()
    assert body["detail"] == "Требуется авторизация"
    assert body["error"]["code"] == "http_401"
    assert body["error"]["request_id"] == "trace-err-1"
    assert response.headers["X-Request-ID"] == "trace-err-1"


def test_real_app_validation_error_envelope():
    with TestClient(real_app) as client:
        response = client.post("/api/v1/leads", json={"name": "", "phone": "1"})
    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "validation_error"
    assert any(field["loc"][-1] == "phone" for field in body["error"]["fields"])
