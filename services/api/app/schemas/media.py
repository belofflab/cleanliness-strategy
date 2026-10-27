"""DTO для медиа и блока «До/После»."""

from pydantic import BaseModel, Field


class MediaOut(BaseModel):
    id: str
    url: str
    content_type: str | None = None


class PresignRequest(BaseModel):
    # master_avatar | before_after | review | other
    owner_type: str = Field(default="other")
    filename: str
    content_type: str | None = None


class PresignResponse(BaseModel):
    key: str
    upload_url: str
    public_url: str


class BeforeAfterOut(BaseModel):
    id: str
    title: str | None = None
    before_url: str
    after_url: str
    # Карточка кейса (ТЗ п.4/9): метаданные выполненного заказа.
    room_type: str | None = None
    area_sqm: int | None = None
    cleaning_type: str | None = None
    cleaners_count: int | None = None
    duration_hours: float | None = None
    cost_text: str | None = None
    district: str | None = None
    task_text: str | None = None
    review_text: str | None = None


class BeforeAfterCreate(BaseModel):
    city_slug: str | None = None
    title: str | None = None
    before_media_id: str
    after_media_id: str
    sort_order: int = 0

