"""Доступ к данным идентификации: пользователи, OTP, refresh-токены."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.auth import OtpCode, RefreshToken, User

__all__ = [
    "bump_otp_attempts",
    "consume_otp",
    "create_otp",
    "create_user",
    "get_active_otp",
    "get_or_create_user",
    "get_refresh",
    "get_user",
    "get_user_by_email",
    "get_user_by_phone",
    "list_users",
    "revoke_family",
    "revoke_refresh",
    "store_refresh",
    "update_user",
]


# ---------- Пользователи ----------
async def get_user_by_phone(db: AsyncSession, phone: str) -> User | None:
    stmt = select(User).where(User.phone == phone)
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_user(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    return await db.get(User, user_id)


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return (await db.execute(stmt)).scalar_one_or_none()


async def get_or_create_user(db: AsyncSession, phone: str, role: str) -> User:
    user = await get_user_by_phone(db, phone)
    if user is None:
        user = User(phone=phone, role=role, is_active=True)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def list_users(
    db: AsyncSession, *, role: str | None = None, limit: int = 50, offset: int = 0
) -> tuple[list[User], int]:
    """Список пользователей с опц. фильтром по роли и пагинацией (админ-CRM)."""
    base = select(User)
    if role is not None:
        base = base.where(User.role == role)
    total = (
        await db.execute(select(func.count()).select_from(base.subquery()))
    ).scalar_one()
    stmt = base.order_by(User.created_at.desc()).limit(limit).offset(offset)
    rows = list((await db.execute(stmt)).scalars().all())
    return rows, total


async def create_user(
    db: AsyncSession,
    *,
    phone: str,
    role: str,
    full_name: str | None = None,
    email: str | None = None,
    password_hash: str | None = None,
) -> User:
    user = User(
        phone=phone,
        role=role,
        full_name=full_name,
        email=email,
        password_hash=password_hash,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(db: AsyncSession, user: User, **fields) -> User:
    """Точечно обновляет переданные (не None) поля пользователя."""
    for key, value in fields.items():
        if value is not None and hasattr(user, key):
            setattr(user, key, value)
    await db.commit()
    await db.refresh(user)
    return user


# ---------- OTP ----------
async def create_otp(
    db: AsyncSession, *, phone: str, code_hash: str, purpose: str, expires_at: datetime
) -> OtpCode:
    otp = OtpCode(phone=phone, code_hash=code_hash, purpose=purpose, expires_at=expires_at)
    db.add(otp)
    await db.commit()
    await db.refresh(otp)
    return otp


async def get_active_otp(db: AsyncSession, *, phone: str, purpose: str) -> OtpCode | None:
    """Последний неиспользованный код для телефона."""
    stmt = (
        select(OtpCode)
        .where(
            OtpCode.phone == phone,
            OtpCode.purpose == purpose,
            OtpCode.consumed_at.is_(None),
        )
        .order_by(OtpCode.created_at.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def consume_otp(db: AsyncSession, otp: OtpCode) -> None:
    otp.consumed_at = datetime.now(otp.expires_at.tzinfo)
    await db.commit()


async def bump_otp_attempts(db: AsyncSession, otp: OtpCode) -> None:
    otp.attempts += 1
    await db.commit()


# ---------- Refresh-токены ----------
async def store_refresh(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    token_hash: str,
    user_agent: str | None,
    expires_at: datetime,
    family_id: uuid.UUID | None = None,
) -> RefreshToken:
    """Сохраняет хеш refresh-токена. Без family_id токен открывает новую семью (устройство)."""
    token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        user_agent=user_agent,
        expires_at=expires_at,
        family_id=family_id,
    )
    db.add(token)
    await db.flush()
    if token.family_id is None:
        token.family_id = token.id
    await db.commit()
    return token


async def get_refresh(db: AsyncSession, token_hash: str) -> RefreshToken | None:
    stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    return (await db.execute(stmt)).scalar_one_or_none()


async def revoke_refresh(db: AsyncSession, token: RefreshToken) -> None:
    token.revoked_at = datetime.now(token.expires_at.tzinfo)
    await db.commit()


async def revoke_family(db: AsyncSession, family_id: uuid.UUID) -> int:
    """Отзывает все живые токены семьи (устройства). Возвращает число отозванных."""
    stmt = (
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=func.now())
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount or 0
