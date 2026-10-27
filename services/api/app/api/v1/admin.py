"""Админ-CRM API (Этап 2): заказы, пользователи (RBAC), клинеры, финансы.

Доступ — только staff (manager/admin). Региональное разграничение: почти у
каждого списка есть необязательный city_slug — без него данные видны
глобально, с ним — по конкретному городу.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import require_roles
from app.api.deps import get_db
from app.core.security import hash_password
from app.models.auth import ALL_ROLES, ROLE_ADMIN, ROLE_MANAGER, User
from app.models.orders import ORDER_STATUSES
from app.modules.identity import repository as users_repo
from app.modules.orders import repository as orders_repo
from app.modules.orders.service import (
    OrderError,
    assign_master,
    change_status,
    convert_lead_to_order,
)
from app.repositories import catalog as catalog_repo
from app.repositories import finance as finance_repo
from app.repositories import leads as leads_repo
from app.repositories import masters as masters_repo
from app.schemas.admin import (
    AdminMasterOut,
    AdminUserOut,
    FinanceCreate,
    FinanceOut,
    FinanceSummary,
    LeadConvert,
    LeadOut,
    LeadPage,
    LeadSummary,
    LeadUpdate,
    MasterCreate,
    MasterUpdate,
    UserCreate,
    UserPage,
    UserUpdate,
)
from app.schemas.orders import MasterAssign, OrderOut, OrderPage, OrderStatusUpdate
from app.services.phones import normalize_phone

router = APIRouter(prefix="/admin", tags=["admin"])

# Любой staff (менеджер/админ) допускается; назначать привилегии — только админ.
_staff = require_roles(ROLE_MANAGER, ROLE_ADMIN)
PRIVILEGED_ROLES = {ROLE_MANAGER, ROLE_ADMIN}


async def _resolve_city_id(db: AsyncSession, city_slug: str | None) -> uuid.UUID | None:
    """city_slug → city_id; None = глобально. 404, если город указан, но не найден."""
    if not city_slug:
        return None
    city = await catalog_repo.get_active_city_by_slug(db, city_slug)
    if city is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Город не найден")
    return city.id


def _ensure_can_set_role(actor: User, target_role: str) -> None:
    if target_role not in ALL_ROLES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Неизвестная роль")
    if target_role in PRIVILEGED_ROLES and actor.role != ROLE_ADMIN:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Назначать роль менеджера/админа может только администратор",
        )


# ============================ Заказы ============================
@router.get("/orders", response_model=OrderPage)
async def list_orders(
    city_slug: str | None = Query(None),
    order_status: str | None = Query(None, alias="status"),
    master_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    city_id = await _resolve_city_id(db, city_slug)
    rows, total = await orders_repo.list_orders(
        db,
        city_id=city_id,
        status=order_status,
        master_id=master_id,
        limit=limit,
        offset=offset,
    )
    return OrderPage(
        items=[OrderOut.from_order(o) for o in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/orders/board", response_model=dict[str, list[OrderOut]])
async def orders_board(
    city_slug: str | None = Query(None),
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    """Канбан: заказы, сгруппированные по статусам (колонка на каждый статус)."""
    city_id = await _resolve_city_id(db, city_slug)
    rows = await orders_repo.list_for_board(db, city_id=city_id)
    board: dict[str, list[OrderOut]] = {s: [] for s in ORDER_STATUSES}
    for order in rows:
        board.setdefault(order.status, []).append(OrderOut.from_order(order))
    return board


@router.get("/orders/{order_id}", response_model=OrderOut)
async def get_order(
    order_id: uuid.UUID,
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    order = await orders_repo.get_order(db, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    return OrderOut.from_order(order)


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
async def set_order_status(
    order_id: uuid.UUID,
    payload: OrderStatusUpdate,
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    if payload.status not in ORDER_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Неизвестный статус")
    order = await orders_repo.get_order(db, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Заказ не найден")
    try:
        await change_status(db, order, payload.status)
    except OrderError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc
    return OrderOut.from_order(order)


@router.patch("/orders/{order_id}/assign", response_model=OrderOut)
async def assign_order_master(
    order_id: uuid.UUID,
    payload: MasterAssign,
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    """Назначить/снять клинера. Мастер должен быть из города заказа."""
    order = await orders_repo.get_order(db, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Заказ не найден")

    master_uuid: uuid.UUID | None = None
    if payload.master_id:
        try:
            master_uuid = uuid.UUID(payload.master_id)
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Некорректный master_id"
            ) from exc
        master = await masters_repo.get_master(db, master_uuid)
        if master is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Мастер не найден")
        if master.city_id != order.city_id:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Мастер из другого города"
            )

    await assign_master(db, order, master_uuid)
    return OrderOut.from_order(order)


# ============================ Лиды ============================
@router.get("/leads", response_model=LeadPage)
async def list_leads(
    city_slug: str | None = Query(None),
    lead_status: str | None = Query(None, alias="status"),
    source: str | None = Query(None, description="Источник: quiz | callback | call | ..."),
    utm_source: str | None = Query(None, description="Рекламный канал (utm_source)"),
    utm_campaign: str | None = Query(None, description="Рекламная кампания (utm_campaign)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    """Входящие заявки: сайт (quiz/callback), звонки (call). Сепарация по городу,
    источнику и рекламной атрибуции — для сегментации в CRM."""
    city_id = await _resolve_city_id(db, city_slug)
    rows, total = await leads_repo.list_leads(
        db,
        city_id=city_id,
        status=lead_status,
        source=source,
        utm_source=utm_source,
        utm_campaign=utm_campaign,
        limit=limit,
        offset=offset,
    )
    return LeadPage(
        items=[LeadOut.from_model(lead) for lead in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/leads/summary", response_model=LeadSummary)
async def leads_summary(
    city_slug: str | None = Query(None),
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    """Дашборд-сегментация лидов: источники, каналы, кампании, статусы, услуги."""
    city_id = await _resolve_city_id(db, city_slug)
    data = await leads_repo.summarize_leads(db, city_id=city_id)
    return LeadSummary(**data)


@router.patch("/leads/{lead_id}", response_model=LeadOut)
async def update_lead(
    lead_id: uuid.UUID,
    payload: LeadUpdate,
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    """Карточка лида (собственная CRM): статус воронки, заметка, ответственный."""
    lead = await leads_repo.get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Лид не найден")

    assignee_value = ...
    if "assignee_id" in payload.model_fields_set:
        if payload.assignee_id:
            try:
                assignee_value = uuid.UUID(payload.assignee_id)
            except ValueError as exc:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, detail="Некорректный assignee_id"
                ) from exc
        else:
            assignee_value = None

    try:
        await leads_repo.update_lead_card(
            db,
            lead,
            status=payload.status,
            manager_note=payload.manager_note,
            assignee_id=assignee_value,
        )
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return LeadOut.from_model(lead)


@router.post("/leads/{lead_id}/convert", response_model=OrderOut)
async def convert_lead(
    lead_id: uuid.UUID,
    payload: LeadConvert,
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    """Создать заказ из лида: расчёт единым прайсингом, лид → converted."""
    lead = await leads_repo.get_lead(db, lead_id)
    if lead is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Лид не найден")

    try:
        order = await convert_lead_to_order(
            db,
            lead,
            service_type=payload.service_type,
            rooms=payload.rooms,
            bathrooms=payload.bathrooms,
            addon_codes=payload.addon_codes,
        )
    except OrderError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=exc.message) from exc

    # Подгружаем связи заказа для сериализации (lead/city/service).
    order = await orders_repo.get_order(db, order.id)
    return OrderOut.from_order(order)


# ====================== Пользователи (RBAC) ======================
@router.get("/users", response_model=UserPage)
async def list_users(
    role: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    rows, total = await users_repo.list_users(db, role=role, limit=limit, offset=offset)
    return UserPage(
        items=[AdminUserOut.from_model(u) for u in rows],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    actor: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    _ensure_can_set_role(actor, payload.role)

    phone = normalize_phone(payload.phone)
    if await users_repo.get_user_by_phone(db, phone) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Пользователь с таким телефоном уже есть"
        )

    password_hash = None
    if payload.role in PRIVILEGED_ROLES:
        if not payload.password:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Для менеджера/админа нужен пароль",
            )
        password_hash = hash_password(payload.password)

    user = await users_repo.create_user(
        db,
        phone=phone,
        role=payload.role,
        full_name=payload.full_name,
        email=payload.email,
        password_hash=password_hash,
    )
    return AdminUserOut.from_model(user)


@router.patch("/users/{user_id}", response_model=AdminUserOut)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    actor: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    user = await users_repo.get_user(db, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    if payload.role is not None:
        _ensure_can_set_role(actor, payload.role)

    user = await users_repo.update_user(
        db,
        user,
        full_name=payload.full_name,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
    )
    return AdminUserOut.from_model(user)


# ======================== Мастера (клинеры) ========================
@router.get("/masters", response_model=list[AdminMasterOut])
async def list_masters(
    city_slug: str | None = Query(None),
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    city_id = await _resolve_city_id(db, city_slug)
    rows = await masters_repo.list_masters(db, city_id=city_id)
    return [AdminMasterOut.from_model(m) for m in rows]


@router.post("/masters", response_model=AdminMasterOut, status_code=status.HTTP_201_CREATED)
async def create_master(
    payload: MasterCreate,
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    city = await catalog_repo.get_active_city_by_slug(db, payload.city_slug)
    if city is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Город не найден")
    phone = normalize_phone(payload.phone) if payload.phone else None
    master = await masters_repo.create_master(
        db,
        city_id=city.id,
        full_name=payload.full_name,
        phone=phone,
        photo_url=payload.photo_url,
    )
    return AdminMasterOut.from_model(master)


@router.patch("/masters/{master_id}", response_model=AdminMasterOut)
async def update_master(
    master_id: uuid.UUID,
    payload: MasterUpdate,
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    master = await masters_repo.get_master(db, master_id)
    if master is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Мастер не найден")
    phone = normalize_phone(payload.phone) if payload.phone else None
    master = await masters_repo.update_master(
        db,
        master,
        full_name=payload.full_name,
        phone=phone,
        photo_url=payload.photo_url,
        is_active=payload.is_active,
    )
    return AdminMasterOut.from_model(master)


# ============================ Финансы ============================
@router.get("/finance", response_model=list[FinanceOut])
async def list_finance(
    city_slug: str | None = Query(None),
    kind: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    city_id = await _resolve_city_id(db, city_slug)
    rows = await finance_repo.list_entries(
        db,
        city_id=city_id,
        kind=kind,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )
    return [FinanceOut.from_model(e) for e in rows]


@router.get("/finance/summary", response_model=FinanceSummary)
async def finance_summary(
    city_slug: str | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    city_id = await _resolve_city_id(db, city_slug)
    data = await finance_repo.summary(
        db, city_id=city_id, date_from=date_from, date_to=date_to
    )
    return FinanceSummary(**data)


@router.post("/finance", response_model=FinanceOut, status_code=status.HTTP_201_CREATED)
async def create_finance(
    payload: FinanceCreate,
    actor: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    if payload.kind not in ("income", "expense"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="kind: income|expense")

    city_id = await _resolve_city_id(db, payload.city_slug)
    order_uuid: uuid.UUID | None = None
    if payload.order_id:
        try:
            order_uuid = uuid.UUID(payload.order_id)
        except ValueError as exc:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Некорректный order_id"
            ) from exc

    entry = await finance_repo.create_entry(
        db,
        kind=payload.kind,
        amount=Decimal(str(payload.amount)),
        category=payload.category,
        city_id=city_id,
        order_id=order_uuid,
        note=payload.note,
        occurred_at=payload.occurred_at,
        created_by_id=actor.id,
    )
    return FinanceOut.from_model(entry)


@router.delete("/finance/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_finance(
    entry_id: uuid.UUID,
    _: User = Depends(_staff),
    db: AsyncSession = Depends(get_db),
):
    entry = await finance_repo.get_entry(db, entry_id)
    if entry is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Проводка не найдена")
    await finance_repo.delete_entry(db, entry)
