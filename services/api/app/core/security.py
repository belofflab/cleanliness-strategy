"""Криптопримитивы аутентификации: пароли, JWT, хеши токенов/кодов.

Изолируем работу с pyjwt/bcrypt здесь, чтобы остальной код не зависел от их API.

Ключи: JWT подписывается JWT_SECRET; хеши OTP-кодов и refresh-токенов считаются
на TOKEN_HMAC_SECRET (отдельный ключ; пусто = JWT_SECRET для совместимости).
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import get_settings

# bcrypt работает максимум с 72 байтами — обрезаем длинные пароли явно.
_BCRYPT_MAX_BYTES = 72


# ---------- Пароли (admin/manager) ----------
def _pw_bytes(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_pw_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_pw_bytes(password), password_hash.encode("utf-8"))
    except ValueError:
        return False


# ---------- OTP-коды и refresh-токены (храним только хеш) ----------
def _hmac_hex(key: str, value: str) -> str:
    return hmac.new(key.encode(), value.encode(), hashlib.sha256).hexdigest()


def hash_secret(value: str) -> str:
    """SHA-256 HMAC на TOKEN_HMAC_SECRET (или JWT_SECRET, если отдельный ключ не задан)."""
    settings = get_settings()
    return _hmac_hex(settings.token_hmac_secret or settings.jwt_secret, value)


def legacy_hash_secret(value: str) -> str | None:
    """Хеш на JWT_SECRET — для refresh-токенов, выданных до ввода TOKEN_HMAC_SECRET.

    None, если отдельный ключ не задан (тогда hash_secret уже использует JWT_SECRET).
    """
    settings = get_settings()
    if not settings.token_hmac_secret:
        return None
    return _hmac_hex(settings.jwt_secret, value)


def verify_secret(value: str, hashed: str) -> bool:
    return hmac.compare_digest(hash_secret(value), hashed)


def generate_numeric_code(length: int = 4) -> str:
    """Числовой OTP-код фиксированной длины."""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def generate_refresh_token() -> str:
    """Криптостойкий случайный refresh-токен (отдаётся клиенту)."""
    return secrets.token_urlsafe(48)


# ---------- JWT access-токены ----------
def create_access_token(*, user_id: str, role: str) -> tuple[str, int]:
    """Возвращает (jwt, expires_in_seconds)."""
    settings = get_settings()
    expires_in = settings.jwt_access_ttl_minutes * 60
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in)).timestamp()),
    }
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token, expires_in


def decode_access_token(token: str) -> dict:
    """Декодирует и валидирует access-токен. Бросает jwt-исключения при ошибке."""
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def refresh_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_ttl_days)
