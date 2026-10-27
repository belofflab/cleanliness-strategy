"""DTO уведомлений и регистрации push-токенов."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.notifications import Notification


class NotificationOut(BaseModel):
    id: str
    title: str
    body: str
    kind: str
    data: dict | None = None
    is_read: bool
    created_at: datetime

    @classmethod
    def from_model(cls, n: Notification) -> "NotificationOut":
        return cls(
            id=str(n.id),
            title=n.title,
            body=n.body,
            kind=n.kind,
            data=n.data,
            is_read=n.is_read,
            created_at=n.created_at,
        )


class PushTokenRegister(BaseModel):
    platform: str = Field(..., pattern="^(ios|android)$")
    expo_token: str = Field(..., min_length=1, max_length=255)
