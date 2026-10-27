"""Тесты лимитера частоты запросов (без Redis: MemoryBackend)."""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request

from app.core import config
from app.core.errors import install_exception_handlers
from app.core.rate_limit import (
    LIMITS,
    MemoryBackend,
    RateLimiter,
    RateLimitExceeded,
    client_ip,
    ip_limit,
    rate_limiter,
)


async def test_memory_backend_counts_within_window_and_resets(monkeypatch):
    backend = MemoryBackend()
    now = [1000.0]
    monkeypatch.setattr("app.core.rate_limit.time.monotonic", lambda: now[0])

    assert (await backend.hit("k", 3, 60))[0] == 1
    assert (await backend.hit("k", 3, 60))[0] == 2
    now[0] += 30
    count, ttl = await backend.hit("k", 3, 60)
    assert count == 3
    assert ttl == 30

    now[0] += 31  # окно истекло — счётчик начинается заново
    count, ttl = await backend.hit("k", 3, 60)
    assert count == 1
    assert ttl == 60


async def test_limiter_raises_after_limit_per_key():
    limiter = RateLimiter(backend=MemoryBackend())
    limit, _ = LIMITS["login_ip"]
    for _ in range(limit):
        await limiter.hit("login_ip", "1.2.3.4")

    with pytest.raises(RateLimitExceeded) as exc_info:
        await limiter.hit("login_ip", "1.2.3.4")
    assert exc_info.value.status_code == 429
    assert exc_info.value.code == "rate_limited"
    assert int(exc_info.value.headers["Retry-After"]) >= 1

    # Другой ключ (IP) не затронут.
    await limiter.hit("login_ip", "5.6.7.8")


async def test_limiter_can_be_disabled_by_settings(monkeypatch):
    monkeypatch.setattr(
        "app.core.rate_limit.get_settings", lambda: config.Settings(rate_limit_enabled=False)
    )
    limiter = RateLimiter(backend=MemoryBackend())
    limit, _ = LIMITS["login_ip"]
    for _ in range(limit + 5):
        await limiter.hit("login_ip", "1.2.3.4")


async def test_limiter_fails_open_when_backend_unavailable():
    class BrokenBackend:
        async def hit(self, key, limit, window_seconds):
            raise ConnectionError("redis down")

    limiter = RateLimiter(backend=BrokenBackend())
    limit, _ = LIMITS["login_ip"]
    for _ in range(limit + 5):
        await limiter.hit("login_ip", "1.2.3.4")  # не бросает: лимитер не роняет сайт


def _request(headers: dict[str, str] | None = None, host: str = "127.0.0.1") -> Request:
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
        "client": (host, 12345),
    }
    return Request(scope)


def test_client_ip_uses_proxy_headers_when_trusted(monkeypatch):
    monkeypatch.setattr(
        "app.core.rate_limit.get_settings", lambda: config.Settings(trust_proxy_headers=True)
    )
    assert client_ip(_request({"X-Forwarded-For": "10.0.0.1, 10.0.0.2"})) == "10.0.0.1"
    assert client_ip(_request({"X-Real-IP": "10.0.0.9", "X-Forwarded-For": "10.0.0.1"})) == "10.0.0.9"
    assert client_ip(_request()) == "127.0.0.1"


def test_client_ip_ignores_proxy_headers_when_not_trusted(monkeypatch):
    monkeypatch.setattr(
        "app.core.rate_limit.get_settings", lambda: config.Settings(trust_proxy_headers=False)
    )
    assert client_ip(_request({"X-Forwarded-For": "10.0.0.1"})) == "127.0.0.1"


def test_ip_limit_dependency_returns_429_with_envelope(monkeypatch):
    monkeypatch.setattr(rate_limiter, "backend", MemoryBackend())

    app = FastAPI()
    install_exception_handlers(app)

    @app.post("/login", dependencies=[Depends(ip_limit("login_ip"))])
    async def login():
        return {"ok": True}

    limit, _ = LIMITS["login_ip"]
    with TestClient(app) as client:
        for _ in range(limit):
            assert client.post("/login").status_code == 200
        blocked = client.post("/login")

    assert blocked.status_code == 429
    assert int(blocked.headers["Retry-After"]) >= 1
    body = blocked.json()
    assert body["detail"] == "Слишком много запросов, попробуйте позже"
    assert body["error"]["code"] == "rate_limited"
