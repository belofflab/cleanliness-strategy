"""Эндпоинт приёма лидов.

POST /leads — принимает заявку с фронта:
1. Сохраняет лид в собственной CRM (статус new) — синхронно и надёжно.
2. Мгновенно уведомляет операторов в Telegram (фоном).
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.rate_limit import ip_limit
from app.repositories import catalog as catalog_repo
from app.repositories import leads as leads_repo
from app.schemas.leads import LeadCreate, LeadCreated
from app.services.telegram import notify_new_lead

router = APIRouter(prefix="/leads", tags=["leads"])


@router.post(
    "",
    response_model=LeadCreated,
    status_code=status.HTTP_201_CREATED,
    # Анти-спам в CRM/Telegram: лимит по IP (app/core/rate_limit.py).
    dependencies=[Depends(ip_limit("leads_ip"))],
)
async def create_lead(
    payload: LeadCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    # Город заявки: явный city_slug либо город по умолчанию (DEFAULT_CITY_SLUG).
    city_slug = payload.city_slug or get_settings().default_city_slug
    city = await catalog_repo.get_active_city_by_slug(db, city_slug)
    city_id = city.id if city else None

    # 1. Надёжно сохраняем заявку.
    lead = await leads_repo.create_lead(
        db,
        name=payload.name,
        phone=payload.phone,
        source=payload.source,
        context=payload.context,
        price=payload.price,
        service_type=payload.service_type,
        utm=payload.utm.model_dump(exclude_none=True) if payload.utm else None,
        yclid=payload.yclid,
        gclid=payload.gclid,
        ym_uid=payload.ym_uid,
        city_id=city_id,
    )

    # 2. Мгновенно уведомляем операторов (Telegram) — цель: реакция за 1–2 мин.
    background_tasks.add_task(notify_new_lead, lead.id)

    return LeadCreated(id=str(lead.id), status=lead.status)

