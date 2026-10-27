"""Celery-приложение (фоновые задачи).

Брокер и backend результатов — Redis. Воркер запускается отдельным контейнером
из того же образа: `celery -A app.core.celery_app.celery_app worker`.
Beat (периодические задачи) — отдельной командой `celery ... beat`.
"""

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "pointclean",
    broker=settings.broker_url,
    backend=settings.result_backend,
    include=[
        "app.tasks.media",
        "app.tasks.reviews",
        "app.tasks.analytics",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Yekaterinburg",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,  # задача подтверждается после выполнения (надёжность)
    worker_max_tasks_per_child=200,
)

# Периодические задачи (Celery beat).
celery_app.conf.beat_schedule = {
    # Синхронизация отзывов из внешних источников (Яндекс/2ГИС/Google).
    "sync-external-reviews": {
        "task": "app.tasks.reviews.sync_reviews",
        "schedule": 3600.0,  # каждый час
    },
}

