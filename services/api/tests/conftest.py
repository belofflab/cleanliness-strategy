"""Общие фикстуры pytest.

Интеграционные тесты требуют живой PostgreSQL (DATABASE_URL).
Если БД недоступна (например, локальный запуск без Docker) — соответствующие
тесты помечаются как skipped, а чистые юнит-тесты продолжают работать.

Запуск интеграционных тестов: `make test-api` (внутри контейнера api с Postgres).
"""

from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text

from app.core.db import AsyncSessionLocal, engine


async def _db_available() -> bool:
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest_asyncio.fixture
async def db_session():
    """Асинхронная сессия БД для интеграционных тестов (skip без Postgres).

    pytest-asyncio выполняет каждый async-тест в собственном event-loop, тогда как
    модульный engine кэширует соединения, привязанные к первому loop. Поэтому перед
    каждым тестом сбрасываем пул через dispose(close=False): создаётся новый пул для
    текущего loop, а старые соединения (в т.ч. открытые sync-TestClient в его loop)
    НЕ закрываются здесь — иначе получаем «Future attached to a different loop».
    """
    await engine.dispose(close=False)
    if not await _db_available():
        pytest.skip(
            "PostgreSQL недоступен — пропускаем интеграционные тесты "
            "(запускайте через `make test-api`)."
        )
    async with AsyncSessionLocal() as session:
        yield session

