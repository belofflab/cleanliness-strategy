"""initial schema: catalog, leads, orders, crm, marketing

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-02

Создаёт полную схему БД платформы: города, услуги, доп.услуги, мастера,
расписания, лиды, заказы, логи CRM, промокоды.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(120), nullable=False, unique=True),
        sa.Column("timezone", sa.String(64), nullable=True),
        sa.Column("price_multiplier", sa.Numeric(4, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", sa.String(40), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("base_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("price_per_room", sa.Numeric(10, 2), nullable=True),
        sa.Column("price_per_bathroom", sa.Numeric(10, 2), nullable=True),
        sa.Column("minutes_base", sa.Integer(), nullable=True),
        sa.Column("minutes_per_room", sa.Integer(), nullable=True),
        sa.Column("minutes_per_bathroom", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("city_id", "type", name="uq_service_city_type"),
    )
    op.create_index("ix_services_city_id", "services", ["city_id"])

    op.create_table(
        "addon_services",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(40), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("minutes", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("city_id", "code", name="uq_addon_city_code"),
    )
    op.create_index("ix_addon_services_city_id", "addon_services", ["city_id"])

    op.create_table(
        "masters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("full_name", sa.String(160), nullable=False),
        sa.Column("rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("photo_url", sa.String(512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_masters_city_id", "masters", ["city_id"])

    op.create_table(
        "master_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("masters.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_booked", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_master_schedules_master_id", "master_schedules", ["master_id"])

    op.create_table(
        "leads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("source", sa.String(40), nullable=True),
        sa.Column("context", sa.String(2000), nullable=True),
        sa.Column("utm", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_leads_city_id", "leads", ["city_id"])

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("service_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("services.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("master_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("masters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("rooms", sa.Integer(), nullable=True),
        sa.Column("bathrooms", sa.Integer(), nullable=True),
        sa.Column("addons", postgresql.JSONB(), nullable=True),
        sa.Column("total_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("est_minutes", sa.Integer(), nullable=True),
        sa.Column("discount_code", sa.String(60), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_orders_lead_id", "orders", ["lead_id"])

    op.create_table(
        "crm_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("lead_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("leads.id", ondelete="CASCADE"), nullable=False),
        sa.Column("request_payload", postgresql.JSONB(), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("amo_deal_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_crm_logs_lead_id", "crm_logs", ["lead_id"])

    op.create_table(
        "promotions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=True),
        sa.Column("code", sa.String(60), nullable=False, unique=True),
        sa.Column("discount_type", sa.String(20), nullable=False),
        sa.Column("value", sa.Numeric(10, 2), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_promotions_city_id", "promotions", ["city_id"])


def downgrade() -> None:
    op.drop_table("promotions")
    op.drop_table("crm_logs")
    op.drop_table("orders")
    op.drop_table("leads")
    op.drop_table("master_schedules")
    op.drop_table("masters")
    op.drop_table("addon_services")
    op.drop_table("services")
    op.drop_table("cities")

