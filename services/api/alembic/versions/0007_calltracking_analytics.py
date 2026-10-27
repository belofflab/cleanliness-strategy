"""calltracking webhook + gclid + service_type

Блоки 2–3 ТЗ по маркетинговым интеграциям:
- call_events — события звонков Calltracking.ru (идемпотентный вебхук,
  привязка к автосозданному лиду);
- leads.gclid — клик-ID Google Ads (сквозная аналитика);
- leads.service_type — вид услуги для сегментации CRM.

Revision ID: 0007_calltracking_analytics
Revises: 0006_quiz_cases_reviews
Create Date: 2026-08-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0007_calltracking_analytics"
down_revision: Union[str, None] = "0006_quiz_cases_reviews"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("leads", sa.Column("gclid", sa.String(length=128), nullable=True))
    op.add_column("leads", sa.Column("service_type", sa.String(length=120), nullable=True))

    op.create_table(
        "call_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("provider", sa.String(length=40), nullable=False, server_default="calltracking"),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("caller_phone", sa.String(length=32), nullable=False),
        sa.Column("tracked_phone", sa.String(length=32), nullable=True),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=True),
        sa.Column("record_url", sa.String(length=1024), nullable=True),
        sa.Column("utm", postgresql.JSONB(), nullable=True),
        sa.Column("ym_uid", sa.String(length=128), nullable=True),
        sa.Column("yclid", sa.String(length=128), nullable=True),
        sa.Column("gclid", sa.String(length=128), nullable=True),
        sa.Column("site_domain", sa.String(length=255), nullable=True),
        sa.Column("raw_payload", postgresql.JSONB(), nullable=True),
        sa.Column(
            "lead_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leads.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "external_id", name="uq_call_provider_external"),
    )
    op.create_index("ix_call_events_lead_id", "call_events", ["lead_id"])


def downgrade() -> None:
    op.drop_index("ix_call_events_lead_id", table_name="call_events")
    op.drop_table("call_events")
    op.drop_column("leads", "service_type")
    op.drop_column("leads", "gclid")
