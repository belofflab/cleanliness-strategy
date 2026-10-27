"""Оркестрация расчёта стоимости поверх БД (переиспользуется калькулятором, букингом и CRM).

Достаёт из БД город/услугу/доп.услуги/промокод и вызывает чистую логику compute_quote().
Возвращает и доменные сущности (для записи заказа), и результат расчёта.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.models.catalog import AddonService, City, Service
from app.modules.pricing.engine import (
    AddonInput,
    PromoInput,
    QuoteResult,
    ServiceInput,
    compute_quote,
)
from app.repositories import catalog as repo

__all__ = ["QuoteBundle", "QuotingError", "build_quote"]


class QuotingError(DomainError):
    """Бизнес-ошибка расчёта (город/услуга не найдены)."""

    status_code = 404
    code = "quoting_error"


@dataclass
class QuoteBundle:
    """Полный результат: и расчёт, и доменные объекты для сохранения заказа."""

    city: City
    service: Service
    addons: list[AddonService]
    result: QuoteResult
    promo_code: str | None


async def build_quote(
    db: AsyncSession,
    *,
    city_slug: str,
    service_type: str,
    rooms: int,
    bathrooms: int,
    addon_codes: list[str] | None,
    promo_code: str | None,
    addon_quantities: dict[str, int] | None = None,
    area_sqm: int | None = None,
    condition: str | None = None,
) -> QuoteBundle:
    city = await repo.get_active_city_by_slug(db, city_slug)
    if city is None:
        raise QuotingError("Город не найден")

    service = await repo.get_service(db, city.id, service_type)
    if service is None:
        raise QuotingError("Услуга недоступна в этом городе")

    # Объединяем допы без количества (старый калькулятор) и с количеством (квиз).
    quantities = dict(addon_quantities or {})
    requested_codes = list(dict.fromkeys([*(addon_codes or []), *quantities.keys()]))
    # Пустой запрос допов = пустой список (list_addons(None) вернул бы ВСЕ допы города
    # и завысил бы цену — фикс краевого случая корректности расчёта).
    addon_models = (
        await repo.list_addons(db, city.id, requested_codes) if requested_codes else []
    )

    promo_input: PromoInput | None = None
    applied_promo: str | None = None
    if promo_code:
        promo = await repo.get_valid_promo(db, city.id, promo_code)
        if promo is not None:
            applied_promo = promo.code
            promo_input = PromoInput(
                code=promo.code,
                discount_type=promo.discount_type,
                value=Decimal(promo.value),
            )

    service_input = ServiceInput(
        name=service.name,
        base_price=Decimal(service.base_price),
        price_per_room=Decimal(service.price_per_room),
        price_per_bathroom=Decimal(service.price_per_bathroom),
        minutes_base=service.minutes_base,
        minutes_per_room=service.minutes_per_room,
        minutes_per_bathroom=service.minutes_per_bathroom,
        price_per_sqm=Decimal(service.price_per_sqm or 0),
    )
    addon_inputs = [
        AddonInput(
            code=a.code,
            name=a.name,
            price=Decimal(a.price),
            minutes=a.minutes,
            # Количество ограничиваем max_qty услуги (защита от абсурдных значений).
            qty=min(max(1, quantities.get(a.code, 1)), a.max_qty or 1),
            unit=a.unit,
        )
        for a in addon_models
    ]

    result = compute_quote(
        service=service_input,
        addons=addon_inputs,
        rooms=rooms,
        bathrooms=bathrooms,
        price_multiplier=Decimal(city.price_multiplier),
        promo=promo_input,
        area_sqm=area_sqm,
        condition=condition,
    )

    return QuoteBundle(
        city=city,
        service=service,
        addons=addon_models,
        result=result,
        promo_code=applied_promo,
    )
