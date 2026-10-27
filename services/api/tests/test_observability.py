"""Тесты наблюдаемости (Этап 5): метрики-middleware и структурные логи.

Не требуют Postgres/Redis — используют DB-независимый эндпоинт /metrics,
чтобы запросы гарантированно отвечали 200 даже без поднятой БД.
"""

from __future__ import annotations

import json

from fastapi.testclient import TestClient
from loguru import logger

from app.main import app

client = TestClient(app)


def test_request_id_and_timing_headers():
    """Middleware добавляет request-id и время ответа в заголовки."""
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID")
    assert response.headers.get("X-Response-Time-ms")


def test_request_id_is_propagated_from_header():
    """Переданный клиентом X-Request-ID сохраняется (сквозная трассировка)."""
    response = client.get("/api/v1/metrics", headers={"X-Request-ID": "trace-123"})
    assert response.headers.get("X-Request-ID") == "trace-123"


def test_metrics_endpoint_counts_requests():
    """/metrics отдаёт счётчики, которые растут после запросов."""
    before = client.get("/api/v1/metrics").json()["requests_total"]
    client.get("/api/v1/metrics")
    after = client.get("/api/v1/metrics").json()["requests_total"]

    assert after > before
    snapshot = client.get("/api/v1/metrics").json()
    assert "requests_by_status_class" in snapshot
    assert "2xx" in snapshot["requests_by_status_class"]
    assert snapshot["avg_duration_ms"] >= 0


def test_access_log_is_structured_json():
    """access-log пишется структурной записью с полями запроса (status_code, latency_ms)."""
    captured: list[str] = []
    sink_id = logger.add(captured.append, serialize=True, level="INFO")
    try:
        client.get("/api/v1/metrics")
    finally:
        logger.remove(sink_id)

    access_lines = []
    for line in captured:
        record = json.loads(line)["record"]
        if record["message"] == "request":
            access_lines.append(record)

    assert access_lines, "не найдено ни одной access-записи 'request'"
    extra = access_lines[-1]["extra"]
    assert extra["method"] == "GET"
    assert extra["path"] == "/api/v1/metrics"
    assert extra["status_code"] == 200
    assert "request_id" in extra
    assert extra["latency_ms"] >= 0


def test_flat_json_sink_emits_request_context(capsys):
    """Плоский JSON-синк выдаёт одну строку с timestamp/level/message + контекст."""
    from app.core.logging import _json_sink

    sink_id = logger.add(_json_sink, level="INFO")
    try:
        logger.bind(request_id="abc", status_code=200).info("flat-line-test")
    finally:
        logger.remove(sink_id)

    out = capsys.readouterr().out.strip().splitlines()
    line = next(ln for ln in out if "flat-line-test" in ln)
    payload = json.loads(line)
    # Плоская структура: поля на верхнем уровне, без вложенного record.
    assert payload["message"] == "flat-line-test"
    assert payload["level"] == "INFO"
    assert "timestamp" in payload and "module" in payload
    assert payload["request_id"] == "abc"
    assert payload["status_code"] == 200
    assert "record" not in payload
