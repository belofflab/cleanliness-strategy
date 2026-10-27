"""Общие примитивы для моделей: UUID-PK и временные метки."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


class UUIDPrimaryKeyMixin:
    """Первичный ключ UUID — удобен для распределённых/сетевых систем."""

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Метка создания записи (UTC, выставляется БД)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

