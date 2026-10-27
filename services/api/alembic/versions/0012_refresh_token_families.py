"""refresh_tokens.family_id: семьи токенов для обнаружения повторного использования

Цепочка ротаций одного устройства получает общий family_id (первый токен
открывает семью своим id). Если клиент предъявляет уже отозванный refresh-токен,
вся семья отзывается — украденный токен не даёт бесконечной сессии.
Существующие токены получают family_id = id (каждый — своя семья).

Revision ID: 0012_refresh_token_families
Revises: 0011_align_schema_with_orm
Create Date: 2026-09-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_refresh_token_families"
down_revision: Union[str, None] = "0011_align_schema_with_orm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "refresh_tokens",
        sa.Column("family_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_refresh_tokens_family_id", "refresh_tokens", ["family_id"])
    op.execute("UPDATE refresh_tokens SET family_id = id WHERE family_id IS NULL")


def downgrade() -> None:
    op.drop_index("ix_refresh_tokens_family_id", table_name="refresh_tokens")
    op.drop_column("refresh_tokens", "family_id")
