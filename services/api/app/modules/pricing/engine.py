"""Логика динамического калькулятора стоимости.

Разделение на два уровня:
1. compute_quote() — ЧИСТАЯ функция (без БД), легко тестируется.
2. build_quote() (quoting.py) — оркестрация: достаёт данные из БД и зовёт compute_quote().

Цена считается в Decimal, чтобы избежать ошибок округления денег.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

__all__ = [
    "AddonInput",
    "CONDITION_COEFFICIENTS",
    "CONDITION_LABELS",
    "MINUTES_PER_SQM",
    "PromoInput",
    "QuoteLine",
    "QuoteResult",
    "ServiceInput",
    "compute_quote",
    "human_minutes",
]


def _money(value: Decimal | float | int) -> Decimal:
    """Округление до копеек/рублей (2 знака) по правилу half-up."""
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class ServiceInput:
    name: str
    base_price: Decimal
    price_per_room: Decimal
    price_per_bathroom: Decimal
    minutes_base: int
    minutes_per_room: int
    minutes_per_bathroom: int
    # Тариф «от площади» (офисная уборка): 0 = не используется.
    price_per_sqm: Decimal = Decimal("0")


@dataclass
class AddonInput:
    code: str
    name: str
    price: Decimal
    minutes: int
    # Количество (створки окон, часы глажки, штуки техники).
    qty: int = 1
    unit: str | None = None


# Коэффициенты состояния помещения (шаг «Состояние» квиза).
# needs_assessment — предварительная оценка по фото: считаем по базовому тарифу
# и помечаем расчёт как предварительный (needs_assessment=True в ответе).
CONDITION_COEFFICIENTS: dict[str, Decimal] = {
    "normal": Decimal("1.00"),
    "neglected": Decimal("1.15"),
    "heavy": Decimal("1.30"),
    "needs_assessment": Decimal("1.00"),
}

CONDITION_LABELS: dict[str, str] = {
    "neglected": "Давно не убирали (+15%)",
    "heavy": "Сильное загрязнение (+30%)",
}

# Оценка времени для тарифов «от площади»: ~30 секунд на м²
# (поддерживающая офисная уборка). Точное время подтверждает менеджер.
MINUTES_PER_SQM = Decimal("0.5")


@dataclass
class PromoInput:
    code: str
    discount_type: str  # "percent" | "fixed"
    value: Decimal


@dataclass
class QuoteLine:
    label: str
    amount: Decimal


@dataclass
class QuoteResult:
    items: list[QuoteLine] = field(default_factory=list)
    subtotal: Decimal = Decimal("0")
    discount: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    est_minutes: int = 0
    # Требуется предварительная оценка по фото — цена предварительная («от»).
    needs_assessment: bool = False


def human_minutes(total_minutes: int) -> str:
    """Преобразует минуты в человекочитаемое «N ч M мин»."""
    if total_minutes <= 0:
        return "—"
    hours, minutes = divmod(total_minutes, 60)
    parts: list[str] = []
    if hours:
        parts.append(f"{hours} ч")
    if minutes:
        parts.append(f"{minutes} мин")
    return " ".join(parts) if parts else "0 мин"


def compute_quote(
    *,
    service: ServiceInput,
    addons: list[AddonInput],
    rooms: int,
    bathrooms: int,
    price_multiplier: Decimal,
    promo: PromoInput | None = None,
    area_sqm: int | None = None,
    condition: str | None = None,
) -> QuoteResult:
    """Чистый расчёт стоимости и времени уборки.

    Формула:
      base = base_price + rooms*price_per_room + bathrooms*price_per_bathroom
             + area*price_per_sqm + Σ (addon.price × addon.qty)
      с_учётом_состояния = base * коэффициент_состояния
      subtotal = с_учётом_состояния * региональный_коэффициент
      total = subtotal - скидка
    """
    result = QuoteResult()

    # 1. Базовая услуга.
    base = Decimal(service.base_price)
    result.items.append(QuoteLine(label=f"Базовая услуга: {service.name}", amount=_money(base)))

    # 2. Комнаты.
    rooms_cost = Decimal(service.price_per_room) * rooms
    if rooms and rooms_cost:
        result.items.append(QuoteLine(label=f"Комнаты × {rooms}", amount=_money(rooms_cost)))

    # 3. Санузлы.
    bath_cost = Decimal(service.price_per_bathroom) * bathrooms
    if bathrooms and bath_cost:
        result.items.append(QuoteLine(label=f"Санузлы × {bathrooms}", amount=_money(bath_cost)))

    # 4. Площадь (тарифы «от м²», прежде всего офисная уборка).
    area_cost = Decimal("0")
    area_minutes = 0
    if area_sqm and Decimal(service.price_per_sqm) > 0:
        area_cost = Decimal(service.price_per_sqm) * area_sqm
        area_minutes = int(MINUTES_PER_SQM * area_sqm)
        result.items.append(QuoteLine(label=f"Площадь × {area_sqm} м²", amount=_money(area_cost)))

    # 5. Доп.услуги (с учётом количества: створки, часы, штуки).
    addons_cost = Decimal("0")
    for addon in addons:
        qty = max(1, int(addon.qty))
        addon_cost = Decimal(addon.price) * qty
        addons_cost += addon_cost
        label = f"Доп: {addon.name}"
        if qty > 1:
            unit_suffix = f" {addon.unit}" if addon.unit else ""
            label += f" × {qty}{unit_suffix}"
        result.items.append(QuoteLine(label=label, amount=_money(addon_cost)))

    base_total = base + rooms_cost + bath_cost + area_cost + addons_cost

    # 6. Состояние помещения (квиз, шаг 4).
    condition_key = condition or "normal"
    condition_coeff = CONDITION_COEFFICIENTS.get(condition_key, Decimal("1.00"))
    result.needs_assessment = condition_key == "needs_assessment"
    if condition_coeff != Decimal("1.00"):
        condition_extra = base_total * (condition_coeff - Decimal("1"))
        label = CONDITION_LABELS.get(condition_key, "Состояние помещения")
        result.items.append(QuoteLine(label=label, amount=_money(condition_extra)))
        base_total += condition_extra

    # 7. Региональный коэффициент.
    subtotal = base_total * Decimal(price_multiplier)
    result.subtotal = _money(subtotal)

    # 8. Скидка по промокоду.
    discount = Decimal("0")
    if promo is not None:
        if promo.discount_type == "percent":
            discount = subtotal * Decimal(promo.value) / Decimal("100")
        elif promo.discount_type == "fixed":
            discount = Decimal(promo.value)
        # Скидка не может превышать сумму.
        discount = min(discount, subtotal)
        result.items.append(QuoteLine(label=f"Скидка ({promo.code})", amount=-_money(discount)))
    result.discount = _money(discount)

    result.total = _money(subtotal - discount)

    # 9. Время уборки (состояние также замедляет работу).
    minutes = Decimal(
        service.minutes_base
        + service.minutes_per_room * rooms
        + service.minutes_per_bathroom * bathrooms
        + area_minutes
        + sum(addon.minutes * max(1, int(addon.qty)) for addon in addons)
    )
    result.est_minutes = int(minutes * condition_coeff)

    return result
