"""orders workflow + master accounts + finance + notifications

Этап 2/4: статус и плановое время заказа, привязка клинера к учётке,
лёгкий финансовый учёт и история уведомлений.

Revision ID: 0005_orders_finance_notify
Revises: 0004_multiregion_marketing_crm
Create Date: 2026-06-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_orders_finance_notify"
down_revision: Union[str, None] = "0004_multiregion_marketing_crm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Заказы: воркфлоу статусов и плановое время ---
    op.add_column(
        "orders",
        sa.Column("status", sa.String(length=30), nullable=False, server_default="new"),
    )
    op.add_column(
        "orders",
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_orders_status", "orders", ["status"])
    # Дефолт нужен только для бэкофилла существующих строк — далее задаёт ORM.
    op.alter_column("orders", "status", server_default=None)

    # --- Мастера: телефон и привязка к учётной записи (мобайл клинера) ---
    op.add_column("masters", sa.Column("phone", sa.String(length=32), nullable=True))
    op.add_column(
        "masters",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_masters_phone", "masters", ["phone"])
    op.create_unique_constraint("uq_masters_user_id", "masters", ["user_id"])
    op.create_foreign_key(
        "fk_masters_user_id",
        "masters",
        "users",
        ["user_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # --- Финансовые проводки (доходы/расходы) ---
    op.create_table(
        "finance_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "city_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cities.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "order_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("orders.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("kind", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=60), nullable=False, server_default="other"),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "created_by_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_finance_entries_city_id", "finance_entries", ["city_id"])
    op.create_index("ix_finance_entries_order_id", "finance_entries", ["order_id"])
    op.create_index("ix_finance_entries_kind", "finance_entries", ["kind"])
    op.create_index("ix_finance_entries_occurred_at", "finance_entries", ["occurred_at"])

    # --- Уведомления (история пушей в мобайле) ---
    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("body", sa.String(length=1000), nullable=False),
        sa.Column("kind", sa.String(length=40), nullable=False, server_default="info"),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")

    op.drop_index("ix_finance_entries_occurred_at", table_name="finance_entries")
    op.drop_index("ix_finance_entries_kind", table_name="finance_entries")
    op.drop_index("ix_finance_entries_order_id", table_name="finance_entries")
    op.drop_index("ix_finance_entries_city_id", table_name="finance_entries")
    op.drop_table("finance_entries")

    op.drop_constraint("fk_masters_user_id", "masters", type_="foreignkey")
    op.drop_constraint("uq_masters_user_id", "masters", type_="unique")
    op.drop_index("ix_masters_phone", table_name="masters")
    op.drop_column("masters", "user_id")
    op.drop_column("masters", "phone")

    op.drop_index("ix_orders_status", table_name="orders")
    op.drop_column("orders", "scheduled_at")
    op.drop_column("orders", "status")
