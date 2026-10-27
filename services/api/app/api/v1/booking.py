"""Эндпоинты букинга.

GET  /booking/masters       — мастера города
GET  /booking/availability  — свободные слоты (опц. дата/мастер)
POST /booking/bookings      — оформить бронирование
"""

from __future__ import annotations

import uuid
from datetime import date

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.core.rate_limit import ip_limit
from app.modules.pricing.engine import human_minutes
from app.repositories import booking as booking_repo
from app.repositories import catalog as catalog_repo
from app.schemas.booking import (
    BookingCreate,
    BookingCreated,
    MasterOut,
    SlotOut,
)
from app.services.booking import BookingError, create_booking
from app.services.telegram import notify_new_lead

router = APIRouter(prefix="/booking", tags=["booking"])


async def _resolve_city_or_404(db: AsyncSession, slug: str | None):
    """Город по slug; пустой slug = город по умолчанию (DEFAULT_CITY_SLUG)."""
    city = await catalog_repo.get_active_city_by_slug(
        db, slug or get_settings().default_city_slug
    )
    if city is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Город не найден")
    return city


@router.get("/masters", response_model=list[MasterOut])
async def get_masters(
    city_slug: str | None = Query(None, description="Пусто = город по умолчанию"),
    db: AsyncSession = Depends(get_db),
):
    """Список мастеров города, отсортированный по рейтингу."""
    city = await _resolve_city_or_404(db, city_slug)
    masters = await booking_repo.list_masters(db, city.id)
    return [
        MasterOut(
            id=str(m.id),
            full_name=m.full_name,
            rating=float(m.rating),
            photo_url=m.photo_url,
        )
        for m in masters
    ]


@router.get("/availability", response_model=list[SlotOut])
async def get_availability(
    city_slug: str | None = Query(None, description="Пусто = город по умолчанию"),
    on_date: date | None = Query(None, alias="date"),
    master_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Свободные слоты мастеров (можно отфильтровать по дате и мастеру)."""
    city = await _resolve_city_or_404(db, city_slug)

    master_uuid: uuid.UUID | None = None
    if master_id:
        try:
            master_uuid = uuid.UUID(master_id)
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Некорректный master_id"
            ) from exc

    slots = await booking_repo.list_available_slots(
        db, city_id=city.id, on_date=on_date, master_id=master_uuid
    )
    return [
        SlotOut(
            id=str(s.id),
            master_id=str(s.master_id),
            master_name=s.master.full_name,
            work_date=s.work_date,
            start_time=s.start_time,
            end_time=s.end_time,
        )
        for s in slots
    ]


@router.post(
    "/bookings",
    response_model=BookingCreated,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(ip_limit("booking_ip"))],
)
async def post_booking(
    payload: BookingCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Оформление бронирования: расчёт → лид → заказ → бронь слота → CRM (фоном)."""
    try:
        lead, order, bundle, slot = await create_booking(
            db,
            name=payload.name,
            phone=payload.phone,
            city_slug=payload.city_slug or get_settings().default_city_slug,
            service_type=payload.service_type,
            rooms=payload.rooms,
            bathrooms=payload.bathrooms,
            addon_codes=payload.addon_codes,
            promo_code=payload.promo_code,
            schedule_id=payload.schedule_id,
            source=payload.source,
        )
    except BookingError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    # Мгновенно уведомляем операторов о брони (Telegram).
    background_tasks.add_task(notify_new_lead, lead.id)

    return BookingCreated(
        order_id=str(order.id),
        lead_id=str(lead.id),
        city=bundle.city.name,
        service=bundle.service.name,
        master_name=slot.master.full_name if slot else None,
        work_date=slot.work_date if slot else None,
        start_time=slot.start_time if slot else None,
        total=float(bundle.result.total),
        est_minutes=bundle.result.est_minutes,
        est_time_human=human_minutes(bundle.result.est_minutes),
    )

