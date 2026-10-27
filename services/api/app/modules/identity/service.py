"""Оркестрация аутентификации: OTP-вход, выпуск и ротация JWT, роли.

Правила безопасности:
- роль `master` (клинер) выдаётся только по карточке мастера, заведённой
  менеджером в CRM с этим телефоном (самозапись клинером невозможна);
- refresh-токены живут семьями: повторное предъявление отозванного токена
  считается кражей — отзывается вся семья устройства;
- хеши OTP/refresh считаются на TOKEN_HMAC_SECRET; токены, выданные под
  старым ключом (JWT_SECRET), принимаются до истечения срока.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError
from app.core.security import (
    create_access_token,
    generate_numeric_code,
    generate_refresh_token,
    hash_secret,
    legacy_hash_secret,
    refresh_expiry,
    verify_password,
    verify_secret,
)
from app.models.auth import ROLE_ADMIN, ROLE_CLIENT, ROLE_MANAGER, ROLE_MASTER, RefreshToken
from app.modules.identity import repository as users_repo
from app.modules.orders import repository as orders_repo
from app.repositories import masters as masters_repo
from app.schemas.auth import TokenPair
from app.services.phones import normalize_phone
from app.services.sms import send_sms

__all__ = [
    "OTP_MAX_ATTEMPTS",
    "OTP_TTL_MINUTES",
    "PASSWORD_LOGIN_ROLES",
    "AuthError",
    "login_with_password",
    "logout",
    "refresh_tokens",
    "request_otp",
    "verify_otp",
]

# Роли, которым разрешён вход по паролю (staff админ-панели).
PASSWORD_LOGIN_ROLES = (ROLE_MANAGER, ROLE_ADMIN)

OTP_TTL_MINUTES = 5
OTP_MAX_ATTEMPTS = 5

MASTER_NOT_REGISTERED = "Учётная запись клинера не найдена — обратитесь к менеджеру"


class AuthError(DomainError):
    status_code = 401
    code = "auth_error"


def _safe_role(role: str) -> str:
    return role if role in (ROLE_CLIENT, ROLE_MASTER) else ROLE_CLIENT


async def _ensure_master_allowed(db: AsyncSession, phone: str) -> None:
    """Роль клинера — только по карточке мастера с этим телефоном (заводит менеджер)."""
    user = await users_repo.get_user_by_phone(db, phone)
    if user is not None and user.role == ROLE_MASTER:
        return
    master = await masters_repo.get_master_by_phone(db, phone)
    if master is None:
        raise AuthError(MASTER_NOT_REGISTERED)
    if master.user_id is not None and (user is None or master.user_id != user.id):
        # Карточка уже привязана к другой учётке — конфликт телефонов, решает менеджер.
        raise AuthError(MASTER_NOT_REGISTERED)


async def request_otp(db: AsyncSession, *, phone: str, role: str) -> tuple[bool, str | None]:
    """Генерирует код, сохраняет хеш и отправляет SMS.

    Возвращает (sent, debug_code). debug_code не пуст только в mock-режиме.
    """
    normalized = normalize_phone(phone)
    if len(normalized) < 11:
        raise AuthError("Некорректный номер телефона")

    # Гейт клинера до отправки SMS: не тратим сообщения на самозапись.
    if _safe_role(role) == ROLE_MASTER:
        await _ensure_master_allowed(db, normalized)

    code = generate_numeric_code(4)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)
    await users_repo.create_otp(
        db,
        phone=normalized,
        code_hash=hash_secret(code),
        purpose="login",
        expires_at=expires_at,
    )

    result = await send_sms(normalized, f"Код входа Точка Чистоты: {code}")

    settings = get_settings()
    # В проде код не раскрываем; в dev/mock — возвращаем для удобства тестов.
    debug_code = code if (result.mocked and settings.environment != "production") else None
    return result.sent, debug_code


async def verify_otp(
    db: AsyncSession, *, phone: str, code: str, role: str, user_agent: str | None
) -> TokenPair:
    normalized = normalize_phone(phone)
    otp = await users_repo.get_active_otp(db, phone=normalized, purpose="login")
    if otp is None:
        raise AuthError("Код не запрашивался или уже использован")

    now = datetime.now(otp.expires_at.tzinfo)
    if otp.expires_at < now:
        raise AuthError("Срок действия кода истёк")
    if otp.attempts >= OTP_MAX_ATTEMPTS:
        raise AuthError("Превышено число попыток, запросите новый код")

    if not verify_secret(code, otp.code_hash):
        await users_repo.bump_otp_attempts(db, otp)
        raise AuthError("Неверный код")

    safe_role = _safe_role(role)
    if safe_role == ROLE_MASTER:
        await _ensure_master_allowed(db, normalized)

    await users_repo.consume_otp(db, otp)

    user = await users_repo.get_user_by_phone(db, normalized)
    if user is None:
        # Роль присваивается при первом входе (client, либо master по карточке мастера).
        user = await users_repo.create_user(db, phone=normalized, role=safe_role)
    elif safe_role == ROLE_MASTER and user.role == ROLE_CLIENT:
        # Клиент стал клинером: менеджер завёл карточку мастера с этим телефоном.
        user = await users_repo.update_user(db, user, role=ROLE_MASTER)
    if not user.is_active:
        raise AuthError("Учётная запись заблокирована")

    # Клинер: связываем учётку с карточкой мастера (по телефону) — для мобайла.
    if user.role == ROLE_MASTER:
        await orders_repo.link_master_by_phone(db, normalized, user.id)

    return await _issue_tokens(db, user_id=user.id, role=user.role, user_agent=user_agent)


async def login_with_password(
    db: AsyncSession, *, login: str, password: str, user_agent: str | None
) -> TokenPair:
    """Вход staff (manager/admin) по телефону или email + паролю — для админ-панели."""
    login = login.strip()
    user = None
    if "@" in login:
        user = await users_repo.get_user_by_email(db, login.lower())
    else:
        user = await users_repo.get_user_by_phone(db, normalize_phone(login))

    # Единое сообщение для несуществующего логина и неверного пароля —
    # не раскрываем, существует ли учётка (анти-энумерация).
    password_hash = user.password_hash if user and user.password_hash else None
    if password_hash is None or not verify_password(password, password_hash):
        raise AuthError("Неверный логин или пароль")
    if user.role not in PASSWORD_LOGIN_ROLES:
        raise AuthError("Вход по паролю доступен только сотрудникам")
    if not user.is_active:
        raise AuthError("Учётная запись заблокирована")

    return await _issue_tokens(db, user_id=user.id, role=user.role, user_agent=user_agent)


async def _find_refresh(db: AsyncSession, refresh_token: str) -> RefreshToken | None:
    """Ищет токен по хешу на текущем ключе, затем — на прежнем (переход на TOKEN_HMAC_SECRET)."""
    stored = await users_repo.get_refresh(db, hash_secret(refresh_token))
    if stored is not None:
        return stored
    legacy_hash = legacy_hash_secret(refresh_token)
    if legacy_hash is None:
        return None
    return await users_repo.get_refresh(db, legacy_hash)


async def refresh_tokens(
    db: AsyncSession, *, refresh_token: str, user_agent: str | None
) -> TokenPair:
    """Ротация: старый refresh отзывается, выдаётся новая пара той же семьи."""
    stored = await _find_refresh(db, refresh_token)
    if stored is None:
        raise AuthError("Невалидный refresh-токен")
    if stored.revoked_at is not None:
        # Повторное использование отозванного токена — признак кражи: гасим всю семью.
        if stored.family_id is not None:
            await users_repo.revoke_family(db, stored.family_id)
        raise AuthError("Refresh-токен отозван")
    if stored.expires_at < datetime.now(stored.expires_at.tzinfo):
        raise AuthError("Refresh-токен истёк")

    user = await users_repo.get_user(db, stored.user_id)
    if user is None or not user.is_active:
        raise AuthError("Пользователь недоступен")

    await users_repo.revoke_refresh(db, stored)
    return await _issue_tokens(
        db,
        user_id=user.id,
        role=user.role,
        user_agent=user_agent,
        family_id=stored.family_id or stored.id,
    )


async def logout(db: AsyncSession, *, refresh_token: str) -> None:
    """Выход с устройства: отзывается вся семья предъявленного refresh-токена."""
    stored = await _find_refresh(db, refresh_token)
    if stored is None:
        return
    if stored.family_id is not None:
        await users_repo.revoke_family(db, stored.family_id)
    elif stored.revoked_at is None:
        await users_repo.revoke_refresh(db, stored)


async def _issue_tokens(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    role: str,
    user_agent: str | None,
    family_id: uuid.UUID | None = None,
) -> TokenPair:
    access, expires_in = create_access_token(user_id=str(user_id), role=role)
    raw_refresh = generate_refresh_token()
    await users_repo.store_refresh(
        db,
        user_id=user_id,
        token_hash=hash_secret(raw_refresh),
        user_agent=user_agent,
        expires_at=refresh_expiry(),
        family_id=family_id,
    )
    return TokenPair(access_token=access, refresh_token=raw_refresh, expires_in=expires_in)
