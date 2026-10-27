"""Лиды и заказы.

Лид (Lead) — сырая заявка с фронта, сохраняется всегда (даже если CRM недоступна).
Заказ (Order) — рассчитанная корзина с итоговой ценой и временем.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.auth import User
    from app.models.catalog import City, Master, Service

# Жизненный цикл заказа (канбан в админке, смена статуса клинером в мобайле).
ORDER_NEW = "new"  # создан, мастер не назначен
ORDER_ASSIGNED = "assigned"  # назначен мастер / запланировано время
ORDER_IN_PROGRESS = "in_progress"  # клинер на объекте, уборка идёт
ORDER_DONE = "done"  # уборка завершена
ORDER_CANCELLED = "cancelled"  # отменён
ORDER_STATUSES = (
    ORDER_NEW,
    ORDER_ASSIGNED,
    ORDER_IN_PROGRESS,
    ORDER_DONE,
    ORDER_CANCELLED,
)
# Разрешённые переходы статусов (защита от некорректной смены).
ORDER_TRANSITIONS = {
    ORDER_NEW: {ORDER_ASSIGNED, ORDER_CANCELLED},
    ORDER_ASSIGNED: {ORDER_IN_PROGRESS, ORDER_CANCELLED, ORDER_NEW},
    ORDER_IN_PROGRESS: {ORDER_DONE, ORDER_CANCELLED},
    ORDER_DONE: set(),
    ORDER_CANCELLED: set(),
}


# Воронка собственной CRM: карточка лида живёт в админке, внешних CRM нет.
LEAD_NEW = "new"                  # заявка только поступила
LEAD_IN_PROGRESS = "in_progress"  # менеджер связался, ведёт диалог
LEAD_CONVERTED = "converted"      # из лида создан заказ
LEAD_REJECTED = "rejected"        # отказ/нецелевой
LEAD_STATUSES = (LEAD_NEW, LEAD_IN_PROGRESS, LEAD_CONVERTED, LEAD_REJECTED)


class Lead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Заявка (сайт/квиз/звонок) — карточка собственной CRM."""

    __tablename__ = "leads"

    city_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False)
    # Источник: quiz | callback | call | booking | ...
    source: Mapped[str] = mapped_column(String(40), default="unknown")
    context: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    # Итог расчёта из квиза-калькулятора (ориентир бюджета для менеджера).
    price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    # Вид услуги (сегментация CRM): поддерживающая/генеральная/послеремонтная/офисная.
    service_type: Mapped[str | None] = mapped_column(String(120), nullable=True)
    utm: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    yclid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gclid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    ym_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Воронка: new | in_progress | converted | rejected (см. LEAD_STATUSES).
    status: Mapped[str] = mapped_column(String(30), default=LEAD_NEW, nullable=False)

    # Собственная CRM: ответственный менеджер и рабочая заметка по лиду.
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    manager_note: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    # Город заявки (только чтение): подгружаем для карточки CRM.
    city: Mapped["City | None"] = relationship("City", lazy="selectin")
    assignee: Mapped["User | None"] = relationship("User", lazy="selectin")
    orders: Mapped[list["Order"]] = relationship(back_populates="lead")


class Order(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Рассчитанный заказ (snapshot выбранных параметров калькулятора)."""

    __tablename__ = "orders"

    lead_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leads.id", ondelete="CASCADE"), nullable=False, index=True
    )
    city_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("services.id", ondelete="RESTRICT"), nullable=False
    )
    master_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("masters.id", ondelete="SET NULL"), nullable=True
    )

    rooms: Mapped[int] = mapped_column(Integer, default=1)
    bathrooms: Mapped[int] = mapped_column(Integer, default=1)
    # Снимок выбранных доп.услуг: [{code, name, price, minutes}]
    addons: Mapped[list | None] = mapped_column(JSONB, nullable=True)

    total_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    est_minutes: Mapped[int] = mapped_column(Integer, default=0)
    discount_code: Mapped[str | None] = mapped_column(String(60), nullable=True)

    # Воркфлоу заказа: канбан в админке + смена статуса клинером в мобайле.
    status: Mapped[str] = mapped_column(
        String(30), default=ORDER_NEW, nullable=False, index=True
    )
    # Плановое время уборки (из выбранного слота либо назначенное менеджером).
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    lead: Mapped["Lead"] = relationship(back_populates="orders")
    # Связи только для чтения (сериализация в админке/мобайле).
    city: Mapped["City"] = relationship("City", lazy="selectin")
    service: Mapped["Service"] = relationship("Service", lazy="selectin")
    master: Mapped["Master | None"] = relationship("Master", lazy="selectin")



