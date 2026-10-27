"""Redis-бэкенд лимитера — против живого Redis (в CI — сервис redis; локально skip)."""

from __future__ import annotations

import uuid

import pytest

from app.core.rate_limit import RedisBackend
from app.core.redis import redis_client

pytestmark = pytest.mark.integration


async def _redis_available() -> bool:
    try:
        return bool(await redis_client.ping())
    except Exception:  # noqa: BLE001 — любой сбой = Redis недоступен
        return False


async def test_redis_backend_counts_atomically_and_sets_ttl():
    if not await _redis_available():
        pytest.skip("Redis недоступен — пропускаем тест Redis-бэкенда лимитера")

    backend = RedisBackend(redis_client)
    key = f"rl:test:{uuid.uuid4().hex}"
    try:
        first_count, first_ttl = await backend.hit(key, 5, 60)
        second_count, second_ttl = await backend.hit(key, 5, 60)
        assert (first_count, second_count) == (1, 2)
        assert 1 <= second_ttl <= first_ttl <= 60
        assert await redis_client.pttl(key) > 0  # окно истечёт само
    finally:
        await redis_client.delete(key)
