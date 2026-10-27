"""multiregion: cities contacts + branches

Revision ID: 0004_multiregion_marketing_crm
Revises: 0003_auth
Create Date: 2026-06-12
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0004_multiregion_marketing_crm"
down_revision: Union[str, None] = "0003_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "cities",
        sa.Column("name_prepositional", sa.String(length=160), nullable=False, server_default="в городе"),
    )
    op.add_column(
        "cities",
        sa.Column("phone", sa.String(length=32), nullable=False, server_default="+7 (912) 395-20-43"),
    )
    op.add_column(
        "cities",
        sa.Column("email", sa.String(length=255), nullable=False, server_default="ow@blanq.tech"),
    )

    op.execute("UPDATE cities SET name_prepositional = 'в Тюмени' WHERE slug = 'tyumen'")
    op.execute("UPDATE cities SET phone = '+7 (912) 395-20-43' WHERE slug = 'tyumen'")
    op.execute("UPDATE cities SET email = 'ow@blanq.tech' WHERE slug = 'tyumen'")

    op.execute("UPDATE cities SET name_prepositional = 'в Уфе' WHERE slug = 'ufa'")
    op.execute("UPDATE cities SET phone = '+7 (993) 138-60-53' WHERE slug = 'ufa'")
    op.execute("UPDATE cities SET email = 'ow@blanq.tech' WHERE slug = 'ufa'")  

    op.alter_column("cities", "name_prepositional", server_default=None)
    op.alter_column("cities", "phone", server_default=None)
    op.alter_column("cities", "email", server_default=None)

    op.create_table(
        "branches",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "city_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("cities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("working_hours", sa.String(length=120), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_branches_city_id", "branches", ["city_id"])

    op.add_column("leads", sa.Column("yclid", sa.String(length=128), nullable=True))
    op.add_column("leads", sa.Column("ym_uid", sa.String(length=128), nullable=True))


def downgrade() -> None:
    op.drop_column("leads", "ym_uid")
    op.drop_column("leads", "yclid")
    op.drop_index("ix_branches_city_id", table_name="branches")
    op.drop_table("branches")
    op.drop_column("cities", "email")
    op.drop_column("cities", "phone")
    op.drop_column("cities", "name_prepositional")
