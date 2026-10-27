"""Push-токены мобильных устройств."""

import uuid

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PushToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Push-токен мобильного устройства (Expo/FCM) для уведомлений."""

    __tablename__ = "push_tokens"

    # user_id появится с таблицей users (Итерация 2); пока nullable.
    user_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)
    # ios | android
    platform: Mapped[str] = mapped_column(String(16), nullable=False)
    expo_token: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

