"""Ограничение частоты запросов (Redis, фиксированное окно).

Защищает чувствительные публичные эндпоинты: запрос OTP (стоимость SMS,
бомбинг), проверку кода и вход по паролю (перебор), приём лидов и букинг
(спам в CRM и Telegram), вебхук звонков. Лимиты — в LIMITS; ключ — IP клиента
(за Nginx: X-Real-IP / X-Forwarded-For) или телефон.

Fail-open: при недоступном Redis запросы пропускаются с предупреждением в
логе — лимитер не должен ронять сайт. В тестах бэкенд подменяется на
MemoryBackend (`monkeypatch.setattr(rate_limiter, "backend", MemoryBackend())`).
"""

from __future__ import annotations

import math
import time
from typing import Protocol

from fastapi import Request
from loguru import logger

from app.core.config import get_settings
from app.core.errors import DomainError

# scope → (лимит запросов, окно в секундах)
LIMITS: dict[str, tuple[int, int]] = {
    "otp_request_phone": (3, 10 * 60),
    "otp_request_ip": (20, 60 * 60),
    "otp_verify_phone": (10, 10 * 60),
    "login_ip": (10, 15 * 60),
    "leads_ip": (20, 60 * 60),
    "booking_ip": (10, 60 * 60),
    "webhook_ip": (120, 60),
}


class RateLimitExceeded(DomainError):
    status_code = 429
    code = "rate_limited"

    def __init__(self, retry_after: int) -> None:
        super().__init__(
            "Слишком много запросов, попробуйте позже",
            headers={"Retry-After": str(retry_after)},
        )
        self.retry_after = retry_after


class RateLimitBackend(Protocol):
    async def hit(self, key: str, limit: int, window_seconds: int) -> tuple[int, int]:
        """Регистрирует обращение; возвращает (счётчик в окне, секунд до сброса окна)."""


class MemoryBackend:
    """In-process бэкенд для тестов и локальной разработки без Redis."""

    def __init__(self) -> None:
        self._hits: dict[str, tuple[int, float]] = {}

    async def hit(self, key: str, limit: int, window_seconds: int) -> tuple[int, int]:
        now = time.monotonic()
        count, expires_at = self._hits.get(key, (0, 0.0))
        if expires_at <= now:
            count, expires_at = 0, now + window_seconds
        count += 1
        self._hits[key] = (count, expires_at)
        return count, max(1, math.ceil(expires_at - now))


# Атомарно: INCR + TTL на первом обращении в окне.
_LUA_HIT = """
local count = redis.call('INCR', KEYS[1])
if count == 1 then redis.call('PEXPIRE', KEYS[1], ARGV[1]) end
local ttl = redis.call('PTTL', KEYS[1])
return {count, ttl}
"""


class RedisBackend:
    def __init__(self, redis) -> None:
        self._redis = redis

    async def hit(self, key: str, limit: int, window_seconds: int) -> tuple[int, int]:
        count, pttl = await self._redis.eval(_LUA_HIT, 1, key, str(window_seconds * 1000))
        ttl = math.ceil(int(pttl) / 1000) if int(pttl) > 0 else window_seconds
        return int(count), max(1, ttl)


class RateLimiter:
    def __init__(self, backend: RateLimitBackend | None = None) -> None:
        self.backend = backend

    def _get_backend(self) -> RateLimitBackend:
        if self.backend is None:
            from app.core.redis import redis_client

            self.backend = RedisBackend(redis_client)
        return self.backend

    async def hit(self, scope: str, key: str) -> None:
        """Регистрирует обращение и бросает RateLimitExceeded при превышении лимита."""
        if not get_settings().rate_limit_enabled:
            return
        limit, window = LIMITS[scope]
        try:
            count, ttl = await self._get_backend().hit(f"rl:{scope}:{key}", limit, window)
        except Exception as exc:  # noqa: BLE001 — fail-open: Redis недоступен
            logger.bind(scope=scope).warning(f"rate_limit_backend_unavailable: {exc}")
            return
        if count > limit:
            logger.bind(scope=scope, key=key, count=count).warning("rate_limited")
            raise RateLimitExceeded(retry_after=ttl)


rate_limiter = RateLimiter()


def client_ip(request: Request) -> str:
    """IP клиента с учётом обратного прокси (TRUST_PROXY_HEADERS)."""
    if get_settings().trust_proxy_headers:
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def ip_limit(scope: str):
    """Зависимость FastAPI: лимит по IP для маршрута (`dependencies=[Depends(ip_limit(...))]`)."""

    async def _dependency(request: Request) -> None:
        await rate_limiter.hit(scope, client_ip(request))

    return _dependency
