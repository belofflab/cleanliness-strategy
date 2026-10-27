"""Мобильное API (Этап 4): заказы клинера/клиента, статусы, профиль, пуши.

Все эндпоинты требуют access-токен (вход по телефону + OTP, см. /auth).
Разграничение по роли:
- master (клинер): видит назначенные ему заказы, двигает их статус;
- client: видит свои заказы (по телефону), статус не меняет.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import get_current_user
from app.api.deps import get_db
from app.models.auth import ROLE_MASTER, User
from app.models.orders import (
    ORDER_ASSIGNED,
    ORDER_DONE,
    ORDER_IN_PROGRESS,
    ORDER_NEW,
    Order,
)
from app.modules.orders import repository as orders_repo
from app.modules.orders.service import OrderError, change_status
from app.repositories import notifications as notifications_repo
from app.schemas.booking import MasterOut
from app.schemas.mobile import MobileProfile
from app.schemas.notifications import NotificationOut, PushTokenRegister
from app.schemas.orders import OrderOut, OrderStatusUpdate

router = APIRouter(prefix="/mobile", tags=["mobile"])

# Группировка статусов для фильтра scope.
ACTIVE_STATUSES = [ORDER_NEW, ORDER_ASSIGNED, ORDER_IN_PROGRESS]
COMPLETED_STATUSES = [ORDER_DONE, "cancelled"]
# Какие переходы разрешены клинеру из мобайла (отмена — за менеджером).
MASTER_ALLOWED_TARGETS = {ORDER_IN_PROGRESS, ORDER_DONE}


def _statuses_for_scope(scope: str) -> list[str] | None:
    if scope == "active":
        return ACTIVE_STATUSES
    if scope == "completed":
        return COMPLETED_STATUSES
    return None  # all


async def _list_my_orders(
    db: AsyncSession, user: User, statuses: list[str] | None
) -> list[Order]:
    if user.role == ROLE_MASTER:
        master = await orders_repo.get_master_by_user_id(db, user.id)
        if master is None:
            return []
        return await orders_repo.list_orders_for_master(db, master.id, statuses=statuses)
    # client (и прочие) — по телефону учётки.
    return await orders_repo.list_orders_for_phone(db, user.phone, statuses=statuses)


async def _get_owned_order(db: AsyncSession, user: User, order_id: uuid.UUID) -> Order:
    order = await orders_repo.get_order(db, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Заказ не найден")

    if user.role == ROLE_MASTER:
        master = await orders_repo.get_master_by_user_id(db, user.id)
        if master is None or order.master_id != master.id:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Заказ не ваш")
    else:
        lead = order.lead
        if lead is None or lead.phone != user.phone:
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Заказ не ваш")
    return order


@router.get("/orders", response_model=list[OrderOut])
async def my_orders(
    scope: str = Query("all", pattern="^(all|active|completed)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Мои заказы. scope=active — текущие, completed — завершённые/отменённые."""
    orders = await _list_my_orders(db, user, _statuses_for_scope(scope))
    return [OrderOut.from_order(o) for o in orders]


@router.get("/orders/{order_id}", response_model=OrderOut)
async def my_order(
    order_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    order = await _get_owned_order(db, user, order_id)
    return OrderOut.from_order(order)


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
async def change_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Клинер меняет статус уборки в реальном времени (assigned→in_progress→done)."""
    if user.role != ROLE_MASTER:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="Менять статус может только клинер"
        )
    if payload.status not in MASTER_ALLOWED_TARGETS:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Клинер может перевести заказ только в работу или в завершён",
        )

    order = await _get_owned_order(db, user, order_id)
    try:
        await change_status(db, order, payload.status)
    except OrderError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return OrderOut.from_order(order)


@router.get("/profile", response_model=MobileProfile)
async def profile(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Профиль пользователя + карточка мастера (если клинер) + счётчик непрочитанных."""
    master_out = None
    if user.role == ROLE_MASTER:
        master = await orders_repo.get_master_by_user_id(db, user.id)
        if master is not None:
            master_out = MasterOut(
                id=str(master.id),
                full_name=master.full_name,
                rating=float(master.rating),
                photo_url=master.photo_url,
            )
    unread = await notifications_repo.count_unread(db, user.id)
    return MobileProfile(
        id=str(user.id),
        phone=user.phone,
        role=user.role,
        full_name=user.full_name,
        master=master_out,
        unread_notifications=unread,
    )


@router.get("/notifications", response_model=list[NotificationOut])
async def notifications(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """История уведомлений пользователя (пуши)."""
    items = await notifications_repo.list_for_user(db, user.id, limit=limit, offset=offset)
    return [NotificationOut.from_model(n) for n in items]


@router.post("/notifications/{notification_id}/read", response_model=NotificationOut)
async def mark_notification_read(
    notification_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    notification = await notifications_repo.get_for_user(db, notification_id, user.id)
    if notification is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Уведомление не найдено")
    notification = await notifications_repo.mark_read(db, notification)
    return NotificationOut.from_model(notification)


@router.post("/push-tokens", status_code=status.HTTP_204_NO_CONTENT)
async def register_push_token(
    payload: PushTokenRegister,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Регистрация push-токена устройства (Expo/FCM) для уведомлений."""
    await notifications_repo.upsert_push_token(
        db, user_id=user.id, platform=payload.platform, expo_token=payload.expo_token
    )
