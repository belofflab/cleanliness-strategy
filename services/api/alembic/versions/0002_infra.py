"""infra: media, reviews, integrations + lead crm retry fields

Revision ID: 0002_infra
Revises: 0001_initial
Create Date: 2026-06-02

Добавляет инфраструктурные таблицы (медиа, отзывы, токены AmoCRM, push)
и поля повторной отправки лидов в CRM.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_infra"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Поля ретраев CRM в leads ---
    op.add_column("leads", sa.Column("crm_attempts", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("leads", sa.Column("crm_next_retry_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("leads", sa.Column("crm_last_error", sa.String(500), nullable=True))
    op.create_index("ix_leads_crm_retry", "leads", ["status", "crm_next_retry_at"])

    # --- media ---
    op.create_table(
        "media",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_type", sa.String(40), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("bucket", sa.String(120), nullable=False),
        sa.Column("key", sa.String(512), nullable=False),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- before_after_pairs ---
    op.create_table(
        "before_after_pairs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("before_media_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("media.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("after_media_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("media.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_before_after_pairs_city_id", "before_after_pairs", ["city_id"])

    # --- review_sources ---
    op.create_table(
        "review_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(20), nullable=False),
        sa.Column("external_place_id", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_review_sources_city_id", "review_sources", ["city_id"])

    # --- reviews ---
    op.create_table(
        "reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("city_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("cities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("review_sources.id", ondelete="SET NULL"), nullable=True),
        sa.Column("provider", sa.String(20), nullable=True),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("author_name", sa.String(160), nullable=False),
        sa.Column("rating", sa.Numeric(2, 1), nullable=True),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("avatar_url", sa.String(1024), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("provider", "external_id", name="uq_review_provider_external"),
    )
    op.create_index("ix_reviews_city_id", "reviews", ["city_id"])

    # --- amocrm_tokens ---
    op.create_table(
        "amocrm_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_domain", sa.String(255), nullable=False, unique=True),
        sa.Column("access_token", sa.String(2048), nullable=False),
        sa.Column("refresh_token", sa.String(2048), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- push_tokens ---
    op.create_table(
        "push_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("platform", sa.String(16), nullable=False),
        sa.Column("expo_token", sa.String(255), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_push_tokens_user_id", "push_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_table("push_tokens")
    op.drop_table("amocrm_tokens")
    op.drop_table("reviews")
    op.drop_table("review_sources")
    op.drop_table("before_after_pairs")
    op.drop_table("media")
    op.drop_index("ix_leads_crm_retry", table_name="leads")
    op.drop_column("leads", "crm_last_error")
    op.drop_column("leads", "crm_next_retry_at")
    op.drop_column("leads", "crm_attempts")

