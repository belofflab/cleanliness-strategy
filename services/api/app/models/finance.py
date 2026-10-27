"""Финансовый учёт: лёгкие записи доходов/расходов (Этап 2).

KISS: одна таблица проводок. Доход — оплата заказа; расход — выплата клинеру,
расходники, транспорт и т.п. Привязка к городу (для фильтра по регионам) и
опционально к заказу (P&L по конкретной уборке).
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin

# Вид проводки.
FINANCE_INCOME = "income"
FINANCE_EXPENSE = "expense"
FINANCE_KINDS = (FINANCE_INCOME, FINANCE_EXPENSE)


class FinanceEntry(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "finance_entries"

    # city_id = NULL → общая (нерегиональная) проводка.
    city_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cities.id", ondelete="SET NULL"), nullable=True, index=True
    )
    order_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True
    )
    # income | expense
    kind: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    # Категория: order_payment | cleaner_payout | supplies | transport | other
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="other")
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    # Кто внёс проводку (менеджер/админ).
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
