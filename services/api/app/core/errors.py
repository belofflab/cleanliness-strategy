"""Доменные ошибки и единый формат ответов об ошибках API.

Формат ответа (обратно совместим: поле `detail` сохранено для существующих
клиентов — лендинг, админка и mobile v1 читают именно его):

    {
      "detail": "<сообщение для пользователя>",
      "error": {"code": "...", "message": "...", "request_id": "...", "fields": [...]}
    }

Роутеры по-прежнему могут явно превращать доменные ошибки в HTTPException с
нужным статусом (например, AuthError → 401 при входе и 400 при OTP).
Необработанный DomainError ловит глобальный обработчик и отдаёт статус/код
класса ошибки. Ошибки валидации — 422 с человекочитаемым `detail` и списком
полей. Любое другое исключение → 500 без утечки внутренних деталей
(стек уходит в лог и Sentry, клиенту — request_id для обращения в поддержку).
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException


class DomainError(Exception):
    """Базовая бизнес-ошибка: сообщение для клиента + машинный код + HTTP-статус."""

    status_code: int = 400
    code: str = "domain_error"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        if code is not None:
            self.code = code
        if status_code is not None:
            self.status_code = status_code
        self.details = details
        self.headers = headers


def error_body(
    *,
    code: str,
    message: str,
    request_id: str | None = None,
    fields: Any = None,
    detail: Any = None,
) -> dict[str, Any]:
    """Тело ответа об ошибке: `detail` (совместимость) + структурный `error`."""
    error: dict[str, Any] = {"code": code, "message": message}
    if request_id:
        error["request_id"] = request_id
    if fields:
        error["fields"] = fields
    return {"detail": message if detail is None else detail, "error": error}


def request_id_of(request: Request) -> str | None:
    """request_id выставляет RequestMetricsMiddleware (request.state)."""
    return getattr(request.state, "request_id", None)


def _validation_fields(exc: RequestValidationError) -> list[dict[str, Any]]:
    # Только безопасные поля: `input` может содержать пароль/телефон, `ctx` — объекты.
    fields: list[dict[str, Any]] = []
    for err in exc.errors():
        fields.append(
            {
                "loc": [str(part) for part in err.get("loc", ())],
                "msg": str(err.get("msg", "")),
                "type": str(err.get("type", "")),
            }
        )
    return fields


def _validation_summary(fields: list[dict[str, Any]]) -> str:
    parts = []
    for field in fields[:5]:
        loc = field["loc"]
        # Опускаем источник (body/query) — пользователю важно имя поля.
        name = ".".join(loc[1:] if len(loc) > 1 else loc) or "запрос"
        parts.append(f"{name}: {field['msg']}")
    return "Некорректные данные запроса: " + "; ".join(parts)


def install_exception_handlers(app: FastAPI) -> None:
    """Регистрирует единые обработчики ошибок на приложении."""

    @app.exception_handler(DomainError)
    async def _domain_error(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                code=exc.code,
                message=exc.message,
                request_id=request_id_of(request),
                fields=exc.details,
            ),
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail
        message = detail if isinstance(detail, str) else "Ошибка запроса"
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                code=f"http_{exc.status_code}",
                message=message,
                request_id=request_id_of(request),
                detail=detail,
            ),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        fields = _validation_fields(exc)
        return JSONResponse(
            status_code=422,
            content=error_body(
                code="validation_error",
                message=_validation_summary(fields),
                request_id=request_id_of(request),
                fields=fields,
            ),
        )

    @app.exception_handler(Exception)
    async def _unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        request_id = request_id_of(request)
        # Стек уже записан RequestMetricsMiddleware (request_failed) и уходит в Sentry;
        # здесь — только факт ответа 500, без внутренних деталей клиенту.
        logger.bind(request_id=request_id, error_type=type(exc).__name__).error("internal_error")
        return JSONResponse(
            status_code=500,
            content=error_body(
                code="internal_error",
                message="Внутренняя ошибка сервера",
                request_id=request_id,
            ),
            headers={"X-Request-ID": request_id} if request_id else None,
        )
