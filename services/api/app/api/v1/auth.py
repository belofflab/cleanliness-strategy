"""Роутер аутентификации: OTP-вход, вход по паролю, обновление и отзыв токенов.

Rate limiting (app/core/rate_limit.py): запрос кода — по IP и по телефону
(анти-бомбинг SMS), проверка кода — по телефону, вход по паролю — по IP (перебор).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import get_db
from app.core.rate_limit import client_ip, ip_limit, rate_limiter
from app.models.auth import User
from app.modules.identity.service import (
    AuthError,
    login_with_password,
    logout,
    refresh_tokens,
    request_otp,
    verify_otp,
)
from app.schemas.auth import (
    OtpRequest,
    OtpRequestResult,
    OtpVerify,
    PasswordLogin,
    RefreshRequest,
    TokenPair,
    UserOut,
)
from app.services.phones import normalize_phone

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/otp/request", response_model=OtpRequestResult)
async def otp_request(payload: OtpRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Запросить код входа по телефону (клиент/мастер)."""
    # Анти-бомбинг SMS: лимиты по IP и по телефону — до создания кода.
    await rate_limiter.hit("otp_request_ip", client_ip(request))
    await rate_limiter.hit("otp_request_phone", normalize_phone(payload.phone))
    try:
        sent, debug_code = await request_otp(db, phone=payload.phone, role=payload.role)
    except AuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return OtpRequestResult(sent=sent, debug_code=debug_code)


@router.post("/otp/verify", response_model=TokenPair)
async def otp_verify(payload: OtpVerify, request: Request, db: AsyncSession = Depends(get_db)):
    """Проверить код и получить пару токенов (access + refresh)."""
    await rate_limiter.hit("otp_verify_phone", normalize_phone(payload.phone))
    try:
        return await verify_otp(
            db,
            phone=payload.phone,
            code=payload.code,
            role=payload.role,
            user_agent=request.headers.get("user-agent"),
        )
    except AuthError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc


@router.post(
    "/login",
    response_model=TokenPair,
    dependencies=[Depends(ip_limit("login_ip"))],
)
async def login(payload: PasswordLogin, request: Request, db: AsyncSession = Depends(get_db)):
    """Вход сотрудника (manager/admin) по телефону/email и паролю — админ-панель."""
    try:
        return await login_with_password(
            db,
            login=payload.login,
            password=payload.password,
            user_agent=request.headers.get("user-agent"),
        )
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """Обновить токены (старый refresh отзывается — ротация; повтор отозванного гасит семью)."""
    try:
        return await refresh_tokens(
            db,
            refresh_token=payload.refresh_token,
            user_agent=request.headers.get("user-agent"),
        )
    except AuthError as exc:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=exc.message) from exc


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout_endpoint(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Отозвать refresh-токены устройства (выход)."""
    await logout(db, refresh_token=payload.refresh_token)


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    """Профиль текущего пользователя по access-токену."""
    return UserOut(id=str(user.id), phone=user.phone, role=user.role, full_name=user.full_name)
