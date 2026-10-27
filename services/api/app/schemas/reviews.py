"""DTO отзывов."""

from datetime import datetime

from pydantic import BaseModel, Field


class ReviewOut(BaseModel):
    id: str
    author_name: str
    rating: float
    text: str
    provider: str
    avatar_url: str | None = None
    # «Прозрачные» отзывы (ТЗ п.6): ссылка на оригинал и вид заказанной уборки.
    source_url: str | None = None
    service_type: str | None = None
    published_at: datetime | None = None

    model_config = {"from_attributes": True}


class ReviewCreate(BaseModel):
    city_slug: str | None = None
    author_name: str = Field(..., max_length=160)
    rating: float = Field(5.0, ge=1, le=5)
    text: str
    avatar_url: str | None = None


class ReviewSyncResult(BaseModel):
    synced: int
    sources: int

