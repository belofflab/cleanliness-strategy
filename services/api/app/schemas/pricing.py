"""DTO калькулятора и каталога (запросы/ответы API)."""

from pydantic import BaseModel, Field


# ---------- Каталог ----------
class CityOut(BaseModel):
    slug: str
    name: str
    price_multiplier: float

    model_config = {"from_attributes": True}


class ServiceOut(BaseModel):
    type: str
    name: str
    base_price: float
    price_per_room: float
    price_per_bathroom: float
    price_per_sqm: float = 0

    model_config = {"from_attributes": True}


class AddonOut(BaseModel):
    code: str
    name: str
    price: float
    # Единица измерения количества («створка», «час», «шт»); None = без количества.
    unit: str | None = None
    max_qty: int = 10

    model_config = {"from_attributes": True}


class CityCatalogOut(BaseModel):
    city: CityOut
    services: list[ServiceOut]
    addons: list[AddonOut]


# ---------- Расчёт ----------
class QuoteAddonIn(BaseModel):
    """Доп.услуга с количеством (створки окон, часы глажки, штуки техники)."""

    code: str = Field(..., examples=["windows"])
    qty: int = Field(1, ge=1, le=500)


class QuoteRequest(BaseModel):
    city_slug: str = Field(..., examples=["tyumen"])
    service_type: str = Field(..., examples=["general"])
    rooms: int = Field(1, ge=0, le=20)
    bathrooms: int = Field(1, ge=0, le=10)
    # Площадь помещения (квиз, шаг 2). Влияет на цену тарифов «от м²» (офисная).
    area_sqm: int | None = Field(None, ge=1, le=10000)
    # Состояние: normal | neglected | heavy | needs_assessment (квиз, шаг 4).
    condition: str | None = Field(None, examples=["normal"])
    # Тип объекта: apartment | house | office | other (квиз, шаг 1) — контекст.
    object_type: str | None = None
    # Доп.услуги без количества (обратная совместимость со старым калькулятором).
    addon_codes: list[str] = Field(default_factory=list)
    # Доп.услуги с количеством (новый квиз). Объединяются с addon_codes.
    addons: list[QuoteAddonIn] = Field(default_factory=list)
    promo_code: str | None = None


class QuoteLineItem(BaseModel):
    label: str
    amount: float


class QuoteResponse(BaseModel):
    city: str
    service: str
    currency: str = "RUB"
    items: list[QuoteLineItem]      # детализация для прозрачности цены
    subtotal: float
    discount: float
    total: float
    est_minutes: int
    est_time_human: str             # «3 ч 30 мин»
    # true — нужна предварительная оценка по фото, цена показывается как «от».
    needs_assessment: bool = False
