"""Зависимости авторизации: текущий пользователь и проверка ролей."""

from __future__ import annotations

import uuid

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.security import decode_access_token
from app.models.auth import User
from app.modules.identity import repository as users_repo

# auto_error=False — сами возвращаем 401 с понятным сообщением.
_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Требуется авторизация")

    try:
        payload = decode_access_token(credentials.credentials)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Токен истёк") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Невалидный токен") from exc

    if payload.get("type") != "access":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Неверный тип токена")

    user = await users_repo.get_user(db, uuid.UUID(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Пользователь недоступен")
    return user


def require_roles(*roles: str):
    """Фабрика зависимости: пускает только пользователей с нужной ролью."""

    async def _checker(user: User = Depends(get_current_user)) -> User:
        if roles and user.role not in roles:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="Недостаточно прав"
            )
        return user

    return _checker

