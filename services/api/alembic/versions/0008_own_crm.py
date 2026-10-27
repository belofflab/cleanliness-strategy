"""own CRM: воронка лидов, ответственный, заметки; удаление AmoCRM

Отказ от внешней CRM (AmoCRM) в пользу собственной в админ-панели:
- статусы лидов crm_* приводятся к воронке new/in_progress/converted/rejected
  (лиды, дошедшие до внешней CRM, считаем взятыми в работу);
- ретраи отправки (crm_attempts/…) и журналы crm_logs/amocrm_tokens удаляются;
- добавляются поля собственной CRM: ответственный менеджер и заметка.

Revision ID: 0008_own_crm
Revises: 0007_calltracking_analytics
Create Date: 2026-08-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0008_own_crm"
down_revision: Union[str, None] = "0007_calltracking_analytics"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Воронка собственной CRM ---
    # Отправленные во внешнюю CRM → «в работе» (менеджер их уже видел),
    # ошибки/выключенная интеграция → «новый» (требуют внимания).
    op.execute("UPDATE leads SET status = 'in_progress' WHERE status = 'sent_to_crm'")
    op.execute(
        "UPDATE leads SET status = 'new' WHERE status IN ('crm_failed', 'crm_disabled')"
    )

    # --- Поля собственной CRM ---
    op.add_column(
        "leads",
        sa.Column("assignee_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_leads_assignee_id", "leads", "users", ["assignee_id"], ["id"], ondelete="SET NULL"
    )
    op.create_index("ix_leads_assignee_id", "leads", ["assignee_id"])
    op.add_column("leads", sa.Column("manager_note", sa.String(length=2000), nullable=True))

    # --- Демонтаж механики внешней CRM ---
    op.drop_column("leads", "crm_attempts")
    op.drop_column("leads", "crm_next_retry_at")
    op.drop_column("leads", "crm_last_error")
    op.drop_table("crm_logs")
    op.drop_table("amocrm_tokens")


def downgrade() -> None:
    op.create_table(
        "amocrm_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_domain", sa.String(length=255), nullable=False, unique=True),
        sa.Column("access_token", sa.String(length=2048), nullable=False),
        sa.Column("refresh_token", sa.String(length=2048), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "crm_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lead_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("leads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("request_payload", postgresql.JSONB(), nullable=True),
        sa.Column("response_payload", postgresql.JSONB(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("amo_deal_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.add_column(
        "leads",
        sa.Column("crm_attempts", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("leads", sa.Column("crm_next_retry_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("leads", sa.Column("crm_last_error", sa.String(length=500), nullable=True))

    op.drop_column("leads", "manager_note")
    op.drop_index("ix_leads_assignee_id", table_name="leads")
    op.drop_constraint("fk_leads_assignee_id", "leads", type_="foreignkey")
    op.drop_column("leads", "assignee_id")
