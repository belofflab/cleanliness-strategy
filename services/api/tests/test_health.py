"""Smoke-тесты доступности API.

Проверяем, что приложение собирается и базовый /health отвечает 200.
Запуск: cd services/api && pytest
"""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_reports_status_and_timestamp():
    """/health всегда отдаёт status + timestamp; код зависит от доступности БД.

    С поднятой БД → 200/ok; без неё (юнит-прогон) → 503/error. В обоих случаях
    тело структурно валидно — это то, что пингует Uptime Kuma.
    """
    response = client.get("/api/v1/health")
    body = response.json()

    assert "timestamp" in body
    assert body["status"] in {"ok", "error"}
    if body["status"] == "ok":
        assert response.status_code == 200
        assert body["database"] == "ok"
    else:
        assert response.status_code == 503
        assert body["database"] == "down"

