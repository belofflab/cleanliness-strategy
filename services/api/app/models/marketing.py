"""Маркетинг: промокоды и индивидуальные предложения."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Promotion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "promotions"

    # city_id = NULL означает глобальную акцию (для всех городов).
    city_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cities.id", ondelete="CASCADE"), nullable=True, index=True
    )
    code: Mapped[str] = mapped_column(String(60), nullable=False, unique=True)
    # percent | fixed
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

