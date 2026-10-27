"""Фоновые задачи сквозной аналитики: офлайн-конверсии в Яндекс.Метрику."""

from __future__ import annotations

from app.core.celery_app import celery_app
from app.tasks.runner import _run_in_task


@celery_app.task(name="app.tasks.analytics.upload_offline_conversion", bind=True, max_retries=3)
def upload_offline_conversion(self, order_id: str) -> dict:
    """Загружает конверсию «Клининг выполнен» по заказу (ретраи с backoff)."""
    from app.services.yandex_offline import upload_order_done_conversion

    result = _run_in_task(lambda: upload_order_done_conversion(order_id))
    if result.get("status") == "error":
        raise self.retry(countdown=60 * (self.request.retries + 1))
    return result
