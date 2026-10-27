"""fix call_events: server_default для created_at, удаление лишней updated_at

Миграция 0007 создала call_events с created_at без server_default (модели
полагаются на дефолт БД из TimestampMixin) и с колонкой updated_at, которой
нет в ORM — вставка события звонка падала NotNullViolation. Данных в таблице
нет (вставки не проходили), поэтому правка безопасна.

Revision ID: 0009_fix_call_events
Revises: 0008_own_crm
Create Date: 2026-08-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_fix_call_events"
down_revision: Union[str, None] = "0008_own_crm"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "call_events",
        "created_at",
        server_default=sa.func.now(),
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
    op.drop_column("call_events", "updated_at")


def downgrade() -> None:
    op.add_column(
        "call_events",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.alter_column(
        "call_events",
        "created_at",
        server_default=None,
        existing_type=sa.DateTime(timezone=True),
        existing_nullable=False,
    )
