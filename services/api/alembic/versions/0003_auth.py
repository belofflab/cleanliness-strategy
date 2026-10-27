"""auth: users, otp_codes, refresh_tokens

Revision ID: 0003_auth
Revises: 0002_infra
Create Date: 2026-06-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_auth"
down_revision: Union[str, None] = "0002_infra"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone", sa.String(32), nullable=False, unique=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("full_name", sa.String(160), nullable=True),
        sa.Column("role", sa.String(20), nullable=False, server_default="client"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_phone", "users", ["phone"])

    op.create_table(
        "otp_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone", sa.String(32), nullable=False),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("purpose", sa.String(30), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_otp_codes_phone", "otp_codes", ["phone"])

    op.create_table(
        "refresh_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_refresh_tokens_user_id", "refresh_tokens", ["user_id"])


def downgrade() -> None:
    op.drop_table("refresh_tokens")
    op.drop_table("otp_codes")
    op.drop_table("users")

