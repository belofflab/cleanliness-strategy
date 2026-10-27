"""DTO для приёма лидов с фронтенда."""

from pydantic import BaseModel, Field


class LeadUtm(BaseModel):
    source: str | None = Field(default=None, max_length=120)
    medium: str | None = Field(default=None, max_length=120)
    campaign: str | None = Field(default=None, max_length=160)
    content: str | None = Field(default=None, max_length=160)
    term: str | None = Field(default=None, max_length=160)


class LeadCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=160, examples=["Иван"])
    phone: str = Field(..., min_length=5, max_length=32, examples=["+7 (917) 000-00-00"])
    # Пусто = город по умолчанию (настройка DEFAULT_CITY_SLUG).
    city_slug: str | None = Field(default=None, examples=["ufa"])
    # Источник заявки на сайте: quiz | callback | hero | footer | cta | header
    source: str = Field(default="unknown", max_length=40)
    # Текст из калькулятора или произвольный контекст
    context: str | None = Field(default=None, max_length=2000)
    # Итог расчёта квиза-калькулятора → ориентир бюджета для менеджера в CRM
    price: float | None = Field(default=None, ge=0, le=10_000_000)
    # Вид услуги (сегментация CRM): человекочитаемое название из квиза
    service_type: str | None = Field(default=None, max_length=120)
    # Маркетинговая атрибуция для сквозной аналитики
    utm: LeadUtm | None = None
    yclid: str | None = Field(default=None, max_length=128)
    gclid: str | None = Field(default=None, max_length=128)
    ym_uid: str | None = Field(default=None, max_length=128)


class LeadCreated(BaseModel):
    id: str
    status: str
    message: str = "Заявка принята, мы свяжемся с вами в ближайшее время"

