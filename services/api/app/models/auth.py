"""Модели аутентификации: пользователи, OTP-коды, refresh-токены."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

# Роли в системе (единая учётка на все клиентские приложения).
ROLE_CLIENT = "client"
ROLE_MASTER = "master"
ROLE_MANAGER = "manager"
ROLE_ADMIN = "admin"
ALL_ROLES = (ROLE_CLIENT, ROLE_MASTER, ROLE_MANAGER, ROLE_ADMIN)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Пользователь. Клиент/мастер входят по телефону (OTP),
    менеджер/админ — по паролю."""

    __tablename__ = "users"

    phone: Mapped[str] = mapped_column(String(32), nullable=False, unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str | None] = mapped_column(String(160), nullable=True)
    role: Mapped[str] = mapped_column(String(20), default=ROLE_CLIENT, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class OtpCode(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Одноразовый код для входа по телефону (хранится только хеш)."""

    __tablename__ = "otp_codes"

    phone: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # login | ... (на будущее: смена телефона и т.п.)
    purpose: Mapped[str] = mapped_column(String(30), default="login")
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class RefreshToken(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Refresh-токен (хранится хеш). Ротация при каждом обновлении."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Семья токенов одного устройства (цепочка ротаций). Повторное использование
    # отозванного токена — признак кражи: отзывается вся семья.
    # NULL — токены, выданные до миграции 0012.
    family_id: Mapped[uuid.UUID | None] = mapped_column(nullable=True, index=True)

