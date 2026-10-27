"""Фоновые задачи работы с медиа (S3 / Yandex Object Storage)."""

from __future__ import annotations

from app.core.celery_app import celery_app


@celery_app.task(name="app.tasks.media.process_media")
def process_media(media_id: str) -> dict:
    """Постобработка загруженного медиа (превью/размеры) — расширяется позже.

    Базовая загрузка идёт синхронно через app.core.s3; тяжёлую обработку
    (ресайз, оптимизация) выносим сюда.
    """
    return {"media_id": media_id, "status": "noop"}

