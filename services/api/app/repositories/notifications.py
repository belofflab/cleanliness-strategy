"""Доступ к данным уведомлений и push-токенов."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.integrations import PushToken
from app.models.notifications import NOTIFY_INFO, Notification


async def create_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    title: str,
    body: str,
    kind: str = NOTIFY_INFO,
    data: dict | None = None,
    sent_at: datetime | None = None,
    commit: bool = True,
) -> Notification:
    """Создаёт уведомление. commit=False — часть единицы работы сервиса (только flush)."""
    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        kind=kind,
        data=data,
        sent_at=sent_at,
    )
    db.add(notification)
    if commit:
        await db.commit()
    else:
        await db.flush()
    await db.refresh(notification)
    return notification


async def list_for_user(
    db: AsyncSession, user_id: uuid.UUID, *, limit: int = 50, offset: int = 0
) -> list[Notification]:
    stmt = (
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await db.execute(stmt)).scalars().all())


async def count_unread(db: AsyncSession, user_id: uuid.UUID) -> int:
    stmt = select(func.count()).where(
        Notification.user_id == user_id, Notification.is_read.is_(False)
    )
    return (await db.execute(stmt)).scalar_one()


async def get_for_user(
    db: AsyncSession, notification_id: uuid.UUID, user_id: uuid.UUID
) -> Notification | None:
    stmt = select(Notification).where(
        Notification.id == notification_id, Notification.user_id == user_id
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def mark_read(db: AsyncSession, notification: Notification) -> Notification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(notification)
    return notification


# ---------- Push-токены устройств ----------
async def upsert_push_token(
    db: AsyncSession, *, user_id: uuid.UUID, platform: str, expo_token: str
) -> PushToken:
    """Регистрирует/переназначает push-токен устройства на пользователя."""
    existing = (
        await db.execute(select(PushToken).where(PushToken.expo_token == expo_token))
    ).scalar_one_or_none()
    if existing is not None:
        existing.user_id = user_id
        existing.platform = platform
        existing.is_active = True
        await db.commit()
        await db.refresh(existing)
        return existing

    token = PushToken(
        user_id=user_id, platform=platform, expo_token=expo_token, is_active=True
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return token
