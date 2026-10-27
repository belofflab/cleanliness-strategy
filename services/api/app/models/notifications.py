"""Уведомления пользователя и история пушей (Этап 4).

Каждое уведомление сохраняется в БД (история в профиле мобильного приложения).
Реальная доставка push (Expo/FCM) — отдельный слой; здесь фиксируем факт и статус.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

# Тип уведомления (для иконки/диплинка в приложении).
NOTIFY_ORDER_ASSIGNED = "order_assigned"
NOTIFY_ORDER_STATUS = "order_status"
NOTIFY_PROMO = "promo"
NOTIFY_INFO = "info"


class Notification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    body: Mapped[str] = mapped_column(String(1000), nullable=False)
    # order_assigned | order_status | promo | info
    kind: Mapped[str] = mapped_column(String(40), default=NOTIFY_INFO, nullable=False)
    # Полезная нагрузка для диплинка (например, {"order_id": "..."}).
    data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Когда фактически отправлен push (NULL — ещё не доставлен).
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
