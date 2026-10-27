"""DTO админ-CRM: пользователи (RBAC), мастера-клинеры, финансы."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.auth import User
from app.models.catalog import Master
from app.models.finance import FINANCE_KINDS, FinanceEntry
from app.models.orders import Lead


# ---------- Пользователи / RBAC ----------
class AdminUserOut(BaseModel):
    id: str
    phone: str
    email: str | None = None
    full_name: str | None = None
    role: str
    is_active: bool
    created_at: datetime

    @classmethod
    def from_model(cls, u: User) -> "AdminUserOut":
        return cls(
            id=str(u.id),
            phone=u.phone,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            is_active=u.is_active,
            created_at=u.created_at,
        )


class UserPage(BaseModel):
    items: list[AdminUserOut]
    total: int
    limit: int
    offset: int


class UserCreate(BaseModel):
    phone: str = Field(..., min_length=5, max_length=32)
    role: str = Field(..., examples=["manager", "master", "client"])
    full_name: str | None = Field(default=None, max_length=160)
    email: str | None = Field(default=None, max_length=255)
    # Обязателен для manager/admin (вход по паролю); для client/master не нужен.
    password: str | None = Field(default=None, min_length=6, max_length=128)


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)
    email: str | None = Field(default=None, max_length=255)
    role: str | None = None
    is_active: bool | None = None


# ---------- Мастера (клинеры) ----------
class AdminMasterOut(BaseModel):
    id: str
    city_id: str
    full_name: str
    phone: str | None = None
    rating: float
    photo_url: str | None = None
    is_active: bool
    has_account: bool  # привязана ли учётка (user_id) — виден ли заказ в мобайле

    @classmethod
    def from_model(cls, m: Master) -> "AdminMasterOut":
        return cls(
            id=str(m.id),
            city_id=str(m.city_id),
            full_name=m.full_name,
            phone=m.phone,
            rating=float(m.rating),
            photo_url=m.photo_url,
            is_active=m.is_active,
            has_account=m.user_id is not None,
        )


class MasterCreate(BaseModel):
    city_slug: str = Field(..., examples=["tyumen"])
    full_name: str = Field(..., min_length=1, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    photo_url: str | None = Field(default=None, max_length=512)


class MasterUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=160)
    phone: str | None = Field(default=None, max_length=32)
    photo_url: str | None = Field(default=None, max_length=512)
    is_active: bool | None = None


# ---------- Финансы ----------
class FinanceCreate(BaseModel):
    kind: str = Field(..., examples=list(FINANCE_KINDS))
    amount: float = Field(..., gt=0)
    category: str = Field(default="other", max_length=60)
    city_slug: str | None = None
    order_id: str | None = None
    note: str | None = Field(default=None, max_length=500)
    occurred_at: datetime | None = None


class FinanceOut(BaseModel):
    id: str
    kind: str
    amount: float
    category: str
    city_id: str | None = None
    order_id: str | None = None
    note: str | None = None
    occurred_at: datetime
    created_at: datetime

    @classmethod
    def from_model(cls, e: FinanceEntry) -> "FinanceOut":
        return cls(
            id=str(e.id),
            kind=e.kind,
            amount=float(e.amount),
            category=e.category,
            city_id=str(e.city_id) if e.city_id else None,
            order_id=str(e.order_id) if e.order_id else None,
            note=e.note,
            occurred_at=e.occurred_at,
            created_at=e.created_at,
        )


class FinanceSummary(BaseModel):
    income: float
    expense: float
    profit: float


# ---------- Лиды (входящие заявки с лендинга) ----------
class LeadOut(BaseModel):
    id: str
    name: str
    phone: str
    source: str
    city: str | None = None
    city_slug: str | None = None
    status: str
    context: str | None = None
    # Сквозная аналитика: рекламная атрибуция и вид услуги (сегментация CRM).
    service_type: str | None = None
    price: float | None = None
    utm: dict | None = None
    yclid: str | None = None
    gclid: str | None = None
    ym_uid: str | None = None
    # Собственная CRM: ответственный и рабочая заметка менеджера.
    assignee_id: str | None = None
    assignee_name: str | None = None
    manager_note: str | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, lead: Lead) -> "LeadOut":
        city = lead.city
        assignee = lead.assignee
        return cls(
            id=str(lead.id),
            name=lead.name,
            phone=lead.phone,
            source=lead.source,
            city=city.name if city else None,
            city_slug=city.slug if city else None,
            status=lead.status,
            context=lead.context,
            service_type=lead.service_type,
            price=float(lead.price) if lead.price is not None else None,
            utm=lead.utm,
            yclid=lead.yclid,
            gclid=lead.gclid,
            ym_uid=lead.ym_uid,
            assignee_id=str(lead.assignee_id) if lead.assignee_id else None,
            assignee_name=(assignee.full_name or assignee.phone) if assignee else None,
            manager_note=lead.manager_note,
            created_at=lead.created_at,
        )


class LeadUpdate(BaseModel):
    """Правка карточки лида менеджером: воронка, заметка, ответственный."""

    status: str | None = Field(default=None, description="new | in_progress | converted | rejected")
    manager_note: str | None = Field(default=None, max_length=2000)
    # null = снять ответственного; поле не передано = не менять.
    assignee_id: str | None = None


class LeadConvert(BaseModel):
    """Создание заказа из лида (город берётся из карточки лида)."""

    service_type: str = Field(..., examples=["general"])
    rooms: int = Field(1, ge=0, le=20)
    bathrooms: int = Field(1, ge=0, le=10)
    addon_codes: list[str] = Field(default_factory=list)


class LeadPage(BaseModel):
    items: list[LeadOut]
    total: int
    limit: int
    offset: int


class LeadSummaryItem(BaseModel):
    value: str
    count: int


class LeadSummary(BaseModel):
    """Сегментация лидов: разрезы для дашборда CRM."""

    by_source: list[LeadSummaryItem]
    by_utm_source: list[LeadSummaryItem]
    by_campaign: list[LeadSummaryItem]
    by_status: list[LeadSummaryItem]
    by_service: list[LeadSummaryItem]
