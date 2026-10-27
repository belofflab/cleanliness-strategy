"""Доступ к данным лидов и логов CRM."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.orders import LEAD_STATUSES, Lead
from app.services.phones import normalize_phone


async def list_leads(
    db: AsyncSession,
    *,
    city_id: uuid.UUID | None = None,
    status: str | None = None,
    source: str | None = None,
    utm_source: str | None = None,
    utm_campaign: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[Lead], int]:
    """Список лидов для админ-CRM: фильтры по городу, статусу, источнику
    (сайт/звонок/квиз) и рекламной атрибуции (utm_source/utm_campaign)."""
    filters = []
    if city_id is not None:
        filters.append(Lead.city_id == city_id)
    if status is not None:
        filters.append(Lead.status == status)
    if source is not None:
        filters.append(Lead.source == source)
    if utm_source is not None:
        filters.append(Lead.utm["source"].astext == utm_source)
    if utm_campaign is not None:
        filters.append(Lead.utm["campaign"].astext == utm_campaign)

    base = select(Lead).where(*filters)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    stmt = (
        base.options(selectinload(Lead.city))
        .order_by(Lead.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = list((await db.execute(stmt)).scalars().all())
    return rows, total


async def create_lead(
    db: AsyncSession,
    *,
    name: str,
    phone: str,
    source: str,
    context: str | None,
    utm: dict | None,
    yclid: str | None,
    ym_uid: str | None,
    city_id: uuid.UUID | None,
    price: float | None = None,
    gclid: str | None = None,
    service_type: str | None = None,
    commit: bool = True,
) -> Lead:
    """Создаёт лид. commit=False — часть единицы работы сервиса (только flush)."""
    # Инвариант: leads.phone всегда в формате +7XXXXXXXXXX. По нему клиент
    # видит свои заказы в мобайле (users.phone нормализован), работает
    # дедуп звонков Calltracking и уведомления клиенту о статусе заказа.
    lead = Lead(
        name=name,
        phone=normalize_phone(phone),
        source=source,
        context=context,
        price=price,
        service_type=service_type,
        utm=utm,
        yclid=yclid,
        gclid=gclid,
        ym_uid=ym_uid,
        city_id=city_id,
        status="new",
    )
    db.add(lead)
    if commit:
        await db.commit()
    else:
        await db.flush()
    await db.refresh(lead)
    return lead


async def get_lead(db: AsyncSession, lead_id: uuid.UUID) -> Lead | None:
    # Сразу подгружаем город (relationship), чтобы избежать ленивой загрузки в async.
    return await db.get(Lead, lead_id, options=[selectinload(Lead.city)])


async def summarize_leads(
    db: AsyncSession, *, city_id: uuid.UUID | None = None
) -> dict[str, list[dict]]:
    """Сегментация лидов для дашборда CRM: разрезы по источнику,
    рекламному каналу (utm_source), кампании и статусу."""
    filters = []
    if city_id is not None:
        filters.append(Lead.city_id == city_id)

    async def _group(expr, key: str) -> list[dict]:
        stmt = (
            select(expr.label("value"), func.count().label("count"))
            .where(*filters)
            .group_by("value")
            .order_by(func.count().desc())
            .limit(20)
        )
        rows = (await db.execute(stmt)).all()
        return [{key: row.value or "—", "count": row.count} for row in rows]

    return {
        "by_source": await _group(Lead.source, "value"),
        "by_utm_source": await _group(Lead.utm["source"].astext, "value"),
        "by_campaign": await _group(Lead.utm["campaign"].astext, "value"),
        "by_status": await _group(Lead.status, "value"),
        "by_service": await _group(Lead.service_type, "value"),
    }


async def set_status(db: AsyncSession, lead: Lead, status: str) -> None:
    lead.status = status
    await db.commit()


async def update_lead_card(
    db: AsyncSession,
    lead: Lead,
    *,
    status: str | None = None,
    manager_note: str | None = None,
    assignee_id=...,
    commit: bool = True,
) -> Lead:
    """Обновление карточки лида менеджером (собственная CRM).

    assignee_id: Ellipsis = «не менять», None = «снять ответственного».
    commit=False — часть единицы работы сервиса (только flush).
    """
    if status is not None:
        if status not in LEAD_STATUSES:
            raise ValueError(f"Неизвестный статус лида: {status}")
        lead.status = status
    if manager_note is not None:
        lead.manager_note = manager_note.strip()[:2000] or None
    if assignee_id is not ...:
        lead.assignee_id = assignee_id
    if commit:
        await db.commit()
    else:
        await db.flush()
    await db.refresh(lead)
    return lead
