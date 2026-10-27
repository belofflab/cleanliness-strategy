"""Эндпоинты каталога и динамического калькулятора.

GET  /cities                      — активные города
GET  /cities/{slug}/services      — услуги и доп.услуги города
POST /pricing/quote               — расчёт стоимости и времени
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.repositories import catalog as repo
from app.schemas.pricing import (
    AddonOut,
    CityCatalogOut,
    CityOut,
    QuoteLineItem,
    QuoteRequest,
    QuoteResponse,
    ServiceOut,
)
from app.modules.pricing.engine import human_minutes
from app.modules.pricing.quoting import QuotingError, build_quote

router = APIRouter()


@router.get("/cities", response_model=list[CityOut], tags=["catalog"])
async def get_cities(db: AsyncSession = Depends(get_db)):
    """Список городов для селектора региона на фронте."""
    cities = await repo.list_active_cities(db)
    return cities


@router.get("/cities/{slug}/services", response_model=CityCatalogOut, tags=["catalog"])
async def get_city_catalog(slug: str, db: AsyncSession = Depends(get_db)):
    """Услуги и доп.услуги конкретного города (мультирегиональность)."""
    city = await repo.get_active_city_by_slug(db, slug)
    if city is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Город не найден")

    services = await repo.list_services(db, city.id)
    addons = await repo.list_addons(db, city.id)
    return CityCatalogOut(
        city=CityOut.model_validate(city),
        services=[ServiceOut.model_validate(s) for s in services],
        addons=[AddonOut.model_validate(a) for a in addons],
    )


@router.post("/pricing/quote", response_model=QuoteResponse, tags=["pricing"])
async def create_quote(payload: QuoteRequest, db: AsyncSession = Depends(get_db)):
    """Динамический расчёт: цена зависит от города, типа уборки и доп.услуг."""
    try:
        bundle = await build_quote(
            db,
            city_slug=payload.city_slug,
            service_type=payload.service_type,
            rooms=payload.rooms,
            bathrooms=payload.bathrooms,
            addon_codes=payload.addon_codes,
            promo_code=payload.promo_code,
            addon_quantities={a.code: a.qty for a in payload.addons},
            area_sqm=payload.area_sqm,
            condition=payload.condition,
        )
    except QuotingError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=exc.message) from exc

    result = bundle.result
    return QuoteResponse(
        city=bundle.city.name,
        service=bundle.service.name,
        items=[QuoteLineItem(label=i.label, amount=float(i.amount)) for i in result.items],
        subtotal=float(result.subtotal),
        discount=float(result.discount),
        total=float(result.total),
        est_minutes=result.est_minutes,
        est_time_human=human_minutes(result.est_minutes),
        needs_assessment=result.needs_assessment,
    )

