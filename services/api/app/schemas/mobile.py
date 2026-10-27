"""DTO мобильного приложения: профиль клинера/клиента."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.booking import MasterOut


class MobileProfile(BaseModel):
    id: str
    phone: str
    role: str
    full_name: str | None = None
    # Заполняется, если пользователь — клинер (привязан к карточке мастера).
    master: MasterOut | None = None
    unread_notifications: int = 0
