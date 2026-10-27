"""Middleware наблюдаемости: request-id, тайминг, структурный access-log и метрики.

KISS-подход без внешних зависимостей:
- на каждый запрос пишется одна структурная запись (метод, путь, статус,
  время ответа, request_id) — это и есть источник метрик для лёгких сборщиков;
- параллельно ведутся in-process счётчики, доступные на `GET /api/v1/metrics`
  для быстрой диагностики (сбрасываются при рестарте процесса).
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Лёгкие in-process метрики. Без Prometheus — простой словарь со счётчиками.
_metrics: dict = {
    "requests_total": 0,
    "requests_by_status_class": defaultdict(int),  # "2xx" | "4xx" | "5xx" ...
    "duration_ms_sum": 0.0,
    "errors_total": 0,  # ответы 5xx
}


def get_metrics_snapshot() -> dict:
    """Текущий снимок метрик процесса (для эндпоинта /metrics)."""
    total = _metrics["requests_total"]
    return {
        "requests_total": total,
        "requests_by_status_class": dict(_metrics["requests_by_status_class"]),
        "errors_total": _metrics["errors_total"],
        "avg_duration_ms": (
            round(_metrics["duration_ms_sum"] / total, 2) if total else 0.0
        ),
    }


def _record(status_code: int, duration_ms: float) -> None:
    _metrics["requests_total"] += 1
    _metrics["requests_by_status_class"][f"{status_code // 100}xx"] += 1
    _metrics["duration_ms_sum"] += duration_ms
    if status_code >= 500:
        _metrics["errors_total"] += 1


class RequestMetricsMiddleware(BaseHTTPMiddleware):
    """Тайминг запроса, структурный access-log и сбор базовых метрик."""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get("x-request-id") or uuid.uuid4().hex
        # Доступен обработчикам ошибок (app/core/errors.py) — отдаём клиенту в error.request_id.
        request.state.request_id = request_id
        start = time.perf_counter()

        # request_id попадёт в extra всех логов, написанных в рамках запроса.
        with logger.contextualize(request_id=request_id):
            try:
                response = await call_next(request)
            except Exception:
                latency_ms = (time.perf_counter() - start) * 1000
                _record(500, latency_ms)
                logger.bind(
                    method=request.method,
                    path=request.url.path,
                    status_code=500,
                    latency_ms=round(latency_ms, 2),
                ).exception("request_failed")
                raise

            latency_ms = (time.perf_counter() - start) * 1000
            _record(response.status_code, latency_ms)
            logger.bind(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                latency_ms=round(latency_ms, 2),
                client=request.client.host if request.client else None,
            ).info("request")

            response.headers["X-Request-ID"] = request_id
            response.headers["X-Response-Time-ms"] = f"{latency_ms:.2f}"
            return response
