"""Healthcheck-эндпоинты.

Используются docker-compose (healthcheck), внешним Nginx и Uptime Kuma,
чтобы понимать, что сервис и его зависимости живы.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.api.middleware import get_metrics_snapshot
from app.core.db import engine
from app.core.redis import redis_client
from app.schemas.system import HealthOut, MetricsOut, ReadinessOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
async def health(response: Response) -> HealthOut:
    """Проверка живости сервиса и доступности БД (для Uptime Kuma / healthcheck).

    Делает быстрый `SELECT 1`. БД доступна → 200 `{status: "ok", ...}`;
    БД недоступна → 503 `{status: "error", ...}` (Uptime Kuma поднимет алерт).
    """
    db_ok = True
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 — любой сбой подключения = БД недоступна
        db_ok = False

    if not db_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthOut(
        status="ok" if db_ok else "error",
        database="ok" if db_ok else "down",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@router.get("/health/ready", response_model=ReadinessOut)
async def readiness() -> ReadinessOut:
    """Глубокая проверка готовности: доступны ли PostgreSQL и Redis.

    Возвращает статус каждой зависимости. Если что-то недоступно —
    помечаем как "down", но не роняем сам эндпоинт.
    """
    db_status = "ok"
    redis_status = "ok"

    # Проверка PostgreSQL: простой SELECT 1.
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 — нам важен любой сбой подключения
        db_status = "down"

    # Проверка Redis: ping.
    try:
        await redis_client.ping()
    except Exception:  # noqa: BLE001
        redis_status = "down"

    overall = "ok" if db_status == "ok" and redis_status == "ok" else "degraded"
    return ReadinessOut(status=overall, database=db_status, redis=redis_status)


@router.get("/metrics", response_model=MetricsOut)
async def metrics() -> MetricsOut:
    """Лёгкие in-process метрики запросов (счётчики, среднее время ответа).

    Не Prometheus: компактный JSON для быстрой диагностики и healthcheck-дашбордов.
    Полноценные метрики снимаются из структурных access-логов сборщиком.
    """
    return MetricsOut(**get_metrics_snapshot())
