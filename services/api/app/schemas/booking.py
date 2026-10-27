"""DTO для мастеров, доступности и бронирования."""

from datetime import date, time

from pydantic import BaseModel, Field


class MasterOut(BaseModel):
    id: str
    full_name: str
    rating: float
    photo_url: str | None = None

    model_config = {"from_attributes": True}


class SlotOut(BaseModel):
    id: str
    master_id: str
    master_name: str
    work_date: date
    start_time: time
    end_time: time


class BookingCreate(BaseModel):
    # Контакт
    name: str = Field(..., min_length=1, max_length=160)
    phone: str = Field(..., min_length=5, max_length=32)
    # Параметры уборки (для расчёта стоимости)
    # Пусто = город по умолчанию (настройка DEFAULT_CITY_SLUG).
    city_slug: str | None = Field(default=None, examples=["ufa"])
    service_type: str = Field(..., examples=["general"])
    rooms: int = Field(1, ge=0, le=20)
    bathrooms: int = Field(1, ge=0, le=10)
    addon_codes: list[str] = Field(default_factory=list)
    promo_code: str | None = None
    # Букинг: выбранный слот мастера (опционально — можно без точного времени)
    schedule_id: str | None = None
    source: str = Field(default="booking", max_length=40)


class BookingCreated(BaseModel):
    order_id: str
    lead_id: str
    city: str
    service: str
    master_name: str | None = None
    work_date: date | None = None
    start_time: time | None = None
    total: float
    est_minutes: int
    est_time_human: str
    status: str = "booked"
    message: str = "Бронирование принято, мы подтвердим детали по телефону"

