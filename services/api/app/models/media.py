"""Медиа (S3) и связанные сущности: аватары мастеров, фото «До/После»."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Media(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Запись о файле в S3 (Yandex Object Storage)."""

    __tablename__ = "media"

    # master_avatar | before_after | review | other
    owner_type: Mapped[str] = mapped_column(String(40), nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True)
    bucket: Mapped[str] = mapped_column(String(120), nullable=False)
    key: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)


class BeforeAfterPair(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Кейс «До/После»: пара фото с одного ракурса + карточка выполненного заказа.

    Метаданные кейса (площадь, вид уборки, состав команды, стоимость, район)
    выводятся на сайте под фотографиями — по ТЗ это главный продающий блок.
    """

    __tablename__ = "before_after_pairs"

    city_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    before_media_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("media.id", ondelete="RESTRICT"), nullable=False
    )
    after_media_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("media.id", ondelete="RESTRICT"), nullable=False
    )

    # --- Карточка кейса (все поля опциональны — выводим только заполненные) ---
    room_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    area_sqm: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cleaning_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    cleaners_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_hours: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    # Стоимость или диапазон текстом: «8 900 ₽» / «от 7 000 до 9 000 ₽».
    cost_text: Mapped[str | None] = mapped_column(String(120), nullable=True)
    district: Mapped[str | None] = mapped_column(String(160), nullable=True)
    task_text: Mapped[str | None] = mapped_column(String(500), nullable=True)
    review_text: Mapped[str | None] = mapped_column(String(500), nullable=True)

    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

