"""DTO заказов — общие для мобайла (клинер/клиент) и админ-CRM."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.orders import ORDER_STATUSES, Order


class OrderOut(BaseModel):
    id: str
    status: str
    city: str | None = None
    city_slug: str | None = None
    service: str | None = None
    service_type: str | None = None
    customer_name: str | None = None
    customer_phone: str | None = None
    master_id: str | None = None
    master_name: str | None = None
    rooms: int
    bathrooms: int
    addons: list[dict] | None = None
    total_price: float
    est_minutes: int
    scheduled_at: datetime | None = None
    created_at: datetime

    @classmethod
    def from_order(cls, order: Order) -> "OrderOut":
        lead = order.lead
        city = order.city
        service = order.service
        master = order.master
        return cls(
            id=str(order.id),
            status=order.status,
            city=city.name if city else None,
            city_slug=city.slug if city else None,
            service=service.name if service else None,
            service_type=service.type if service else None,
            customer_name=lead.name if lead else None,
            customer_phone=lead.phone if lead else None,
            master_id=str(order.master_id) if order.master_id else None,
            master_name=master.full_name if master else None,
            rooms=order.rooms,
            bathrooms=order.bathrooms,
            addons=order.addons,
            total_price=float(order.total_price),
            est_minutes=order.est_minutes,
            scheduled_at=order.scheduled_at,
            created_at=order.created_at,
        )


class OrderPage(BaseModel):
    items: list[OrderOut]
    total: int
    limit: int
    offset: int


class OrderStatusUpdate(BaseModel):
    status: str = Field(..., examples=list(ORDER_STATUSES))


class MasterAssign(BaseModel):
    # null — снять назначение
    master_id: str | None = None
