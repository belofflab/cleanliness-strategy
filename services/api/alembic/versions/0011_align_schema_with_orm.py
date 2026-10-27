"""align schema with ORM: NOT NULL для колонок с дефолтами ORM, уникальный индекс users.phone

`alembic check` (контроль дрейфа в CI) показал расхождения между миграциями и
моделями: ряд колонок объявлен в ORM как обязательный (Mapped[...] с default),
а в БД остался nullable с ранних ревизий; users.phone в ORM — уникальный индекс
(unique=True, index=True), а в БД — unique-constraint + обычный индекс.

Приложение всегда записывает значения (дефолты ORM), поэтому NULL в этих
колонках быть не должно; на всякий случай бэкфиллим дефолтами перед SET NOT NULL.

Revision ID: 0011_align_schema_with_orm
Revises: 0010_normalize_lead_phones
Create Date: 2026-09-11
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011_align_schema_with_orm"
down_revision: Union[str, None] = "0010_normalize_lead_phones"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (таблица, колонка, тип, SQL-литерал дефолта для бэкфилла)
_NOT_NULL_COLUMNS: list[tuple[str, str, sa.types.TypeEngine, str]] = [
    ("services", "price_per_room", sa.Numeric(10, 2), "0"),
    ("services", "price_per_bathroom", sa.Numeric(10, 2), "0"),
    ("services", "minutes_base", sa.Integer(), "0"),
    ("services", "minutes_per_room", sa.Integer(), "0"),
    ("services", "minutes_per_bathroom", sa.Integer(), "0"),
    ("addon_services", "minutes", sa.Integer(), "0"),
    ("cities", "timezone", sa.String(64), "'Asia/Yekaterinburg'"),
    ("masters", "rating", sa.Numeric(3, 2), "5.00"),
    ("leads", "source", sa.String(40), "'unknown'"),
    ("orders", "rooms", sa.Integer(), "1"),
    ("orders", "bathrooms", sa.Integer(), "1"),
    ("orders", "est_minutes", sa.Integer(), "0"),
    ("otp_codes", "purpose", sa.String(30), "'login'"),
    ("reviews", "provider", sa.String(20), "'manual'"),
    ("reviews", "rating", sa.Numeric(2, 1), "5.0"),
    ("before_after_pairs", "sort_order", sa.Integer(), "0"),
]


def upgrade() -> None:
    for table, column, col_type, default_sql in _NOT_NULL_COLUMNS:
        op.execute(f"UPDATE {table} SET {column} = {default_sql} WHERE {column} IS NULL")
        op.alter_column(table, column, existing_type=col_type, nullable=False)

    # users.phone: один уникальный индекс вместо unique-constraint + обычного индекса.
    inspector = sa.inspect(op.get_bind())
    for constraint in inspector.get_unique_constraints("users"):
        if constraint["column_names"] == ["phone"] and constraint["name"]:
            op.drop_constraint(constraint["name"], "users", type_="unique")
    for index in inspector.get_indexes("users"):
        if index["name"] == "ix_users_phone" and not index["unique"]:
            op.drop_index("ix_users_phone", table_name="users")
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_users_phone", table_name="users")
    op.create_index("ix_users_phone", "users", ["phone"])
    op.create_unique_constraint("users_phone_key", "users", ["phone"])

    for table, column, col_type, _ in reversed(_NOT_NULL_COLUMNS):
        op.alter_column(table, column, existing_type=col_type, nullable=True)
