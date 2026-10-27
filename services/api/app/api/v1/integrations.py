"""Интеграции: вебхук звонков Calltracking.ru.

POST /integrations/calltracking/webhook — уведомления о звонках (?secret=...).
Звонок сохраняется событием и автоматически становится карточкой лида
в собственной CRM (раздел «Лиды» админки).
"""

from __future__ import annotations

import hmac
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.rate_limit import ip_limit
from app.schemas.system import CallWebhookResult
from app.services.calltracking import CallWebhookError, process_call_event
from app.services.telegram import notify_new_lead

logger = logging.getLogger(__name__)

calltracking_router = APIRouter(prefix="/integrations/calltracking", tags=["integrations"])
_webhook_limit = [Depends(ip_limit("webhook_ip"))]


async def _extract_webhook_payload(request: Request) -> dict:
    """Собирает параметры уведомления из JSON-тела, form-data и query-строки.

    Calltracking может слать данные любым из способов (настраивается в кабинете) —
    принимаем все, приоритет у тела запроса.
    """
    payload: dict = dict(request.query_params)
    payload.pop("secret", None)

    content_type = (request.headers.get("content-type") or "").lower()
    try:
        if "application/json" in content_type:
            body = await request.json()
            if isinstance(body, dict):
                payload.update(body)
        elif "form" in content_type:
            form = await request.form()
            payload.update({k: v for k, v in form.items() if isinstance(v, str)})
        elif await request.body():
            # Тип не указан — пробуем JSON, молча пропускаем при неудаче.
            body = await request.json()
            if isinstance(body, dict):
                payload.update(body)
    except Exception:  # noqa: BLE001 — битое тело не должно ронять вебхук
        logger.warning("Calltracking webhook: тело запроса не распарсилось")

    return payload


@calltracking_router.post("/webhook", response_model=CallWebhookResult, dependencies=_webhook_limit)
@calltracking_router.get(  # некоторые кабинеты шлют GET
    "/webhook", include_in_schema=False, response_model=CallWebhookResult, dependencies=_webhook_limit
)
async def calltracking_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    secret: str = Query(default=""),
    db: AsyncSession = Depends(get_db),
):
    """Приём события звонка: событие → лид в собственной CRM (идемпотентно)."""
    settings = get_settings()
    if not settings.calltracking_webhook_secret:
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Вебхук не настроен: задайте CALLTRACKING_WEBHOOK_SECRET",
        )
    if not hmac.compare_digest(secret, settings.calltracking_webhook_secret):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Неверный секрет вебхука")

    payload = await _extract_webhook_payload(request)
    try:
        result = await process_call_event(db, payload)
    except CallWebhookError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc

    # Новый лид — пингуем операторов в Telegram (как лиды с сайта).
    if result.get("lead_created") and result.get("lead_id"):
        background_tasks.add_task(notify_new_lead, uuid.UUID(result["lead_id"]))

    return result
