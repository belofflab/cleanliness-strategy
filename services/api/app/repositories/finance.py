"""Доступ к финансовым проводкам (доходы/расходы) — админ-CRM."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.finance import FINANCE_EXPENSE, FINANCE_INCOME, FinanceEntry


def _apply_filters(stmt, *, city_id, kind, order_id, date_from, date_to):
    if city_id is not None:
        stmt = stmt.where(FinanceEntry.city_id == city_id)
    if kind is not None:
        stmt = stmt.where(FinanceEntry.kind == kind)
    if order_id is not None:
        stmt = stmt.where(FinanceEntry.order_id == order_id)
    if date_from is not None:
        stmt = stmt.where(FinanceEntry.occurred_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(FinanceEntry.occurred_at <= date_to)
    return stmt


async def create_entry(
    db: AsyncSession,
    *,
    kind: str,
    amount: Decimal,
    category: str,
    city_id: uuid.UUID | None,
    order_id: uuid.UUID | None,
    note: str | None,
    occurred_at: datetime | None,
    created_by_id: uuid.UUID | None,
) -> FinanceEntry:
    entry = FinanceEntry(
        kind=kind,
        amount=amount,
        category=category,
        city_id=city_id,
        order_id=order_id,
        note=note,
        created_by_id=created_by_id,
    )
    if occurred_at is not None:
        entry.occurred_at = occurred_at
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def get_entry(db: AsyncSession, entry_id: uuid.UUID) -> FinanceEntry | None:
    return await db.get(FinanceEntry, entry_id)


async def delete_entry(db: AsyncSession, entry: FinanceEntry) -> None:
    await db.delete(entry)
    await db.commit()


async def list_entries(
    db: AsyncSession,
    *,
    city_id: uuid.UUID | None = None,
    kind: str | None = None,
    order_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[FinanceEntry]:
    stmt = _apply_filters(
        select(FinanceEntry),
        city_id=city_id,
        kind=kind,
        order_id=order_id,
        date_from=date_from,
        date_to=date_to,
    )
    stmt = stmt.order_by(FinanceEntry.occurred_at.desc()).limit(limit).offset(offset)
    return list((await db.execute(stmt)).scalars().all())


async def summary(
    db: AsyncSession,
    *,
    city_id: uuid.UUID | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> dict:
    """Свод доходов/расходов/прибыли по фильтру (для дашборда финансов)."""
    stmt = _apply_filters(
        select(FinanceEntry.kind, func.coalesce(func.sum(FinanceEntry.amount), 0)),
        city_id=city_id,
        kind=None,
        order_id=None,
        date_from=date_from,
        date_to=date_to,
    ).group_by(FinanceEntry.kind)

    totals = {row[0]: float(row[1]) for row in (await db.execute(stmt)).all()}
    income = totals.get(FINANCE_INCOME, 0.0)
    expense = totals.get(FINANCE_EXPENSE, 0.0)
    return {
        "income": round(income, 2),
        "expense": round(expense, 2),
        "profit": round(income - expense, 2),
    }
