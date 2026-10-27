"""Отзывы и подключённые внешние источники (Яндекс/2ГИС/Google)."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ReviewSource(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Подключённый источник отзывов для города."""

    __tablename__ = "review_sources"

    city_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # yandex | 2gis | google
    provider: Mapped[str] = mapped_column(String(20), nullable=False)
    external_place_id: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class Review(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Отзыв (собранный из внешнего источника или добавленный вручную)."""

    __tablename__ = "reviews"
    __table_args__ = (
        # Идемпотентность синхронизации: один и тот же отзыв не дублируется.
        UniqueConstraint("provider", "external_id", name="uq_review_provider_external"),
    )

    city_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("review_sources.id", ondelete="SET NULL"), nullable=True
    )
    provider: Mapped[str] = mapped_column(String(20), default="manual")
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    author_name: Mapped[str] = mapped_column(String(160), nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(2, 1), default=5.0)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    avatar_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Ссылка на оригинал отзыва на площадке («Смотреть оригинал» на сайте).
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    # Вид заказанной уборки — выводится в карточке отзыва по ТЗ.
    service_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_published: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

