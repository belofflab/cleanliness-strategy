"""Фоновая синхронизация отзывов из внешних источников.

Провайдеры: Яндекс.Карты / 2ГИС / Google Maps. Источники хранятся в review_sources,
собранные отзывы — в reviews (идемпотентно по provider+external_id).
Реальные коннекторы подключаются в соответствующей итерации; сейчас — каркас.
"""

from __future__ import annotations

import asyncio

from app.core.celery_app import celery_app


@celery_app.task(name="app.tasks.reviews.sync_reviews")
def sync_reviews() -> dict:
    """Обходит активные review_sources и upsert-ит свежие отзывы."""
    from app.core.db import AsyncSessionLocal
    from app.services.reviews_sync import sync_all

    async def _run() -> tuple[int, int]:
        async with AsyncSessionLocal() as db:
            return await sync_all(db)

    try:
        created, sources = asyncio.run(_run())
        return {"status": "ok", "synced": created, "sources": sources}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "detail": str(exc)}

