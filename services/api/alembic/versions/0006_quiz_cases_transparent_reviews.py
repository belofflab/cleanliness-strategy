"""quiz calculator + real cases + transparent reviews

ТЗ (аудит по сайту):
- п.8: квиз-калькулятор — тариф за м² у услуг, единицы/лимиты количества у
  доп.услуг, итог расчёта у лида (бюджет сделки в CRM);
- п.4/9: кейсы «До/После» — метаданные выполненного заказа;
- п.6: «прозрачные» отзывы — ссылка на оригинал и вид уборки.

Revision ID: 0006_quiz_cases_reviews
Revises: 0005_orders_finance_notify
Create Date: 2026-07-27
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_quiz_cases_reviews"
down_revision: Union[str, None] = "0005_orders_finance_notify"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Услуги: тариф за квадратный метр (офисная уборка) ---
    op.add_column(
        "services",
        sa.Column("price_per_sqm", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.alter_column("services", "price_per_sqm", server_default=None)

    # --- Доп.услуги: количество (створки/часы/штуки) ---
    op.add_column("addon_services", sa.Column("unit", sa.String(length=40), nullable=True))
    op.add_column(
        "addon_services",
        sa.Column("max_qty", sa.Integer(), nullable=False, server_default="10"),
    )
    op.alter_column("addon_services", "max_qty", server_default=None)

    # --- Лиды: итог расчёта квиза (бюджет сделки в AmoCRM) ---
    op.add_column("leads", sa.Column("price", sa.Numeric(10, 2), nullable=True))

    # --- Кейсы «До/После»: карточка выполненного заказа ---
    op.add_column("before_after_pairs", sa.Column("room_type", sa.String(length=120), nullable=True))
    op.add_column("before_after_pairs", sa.Column("area_sqm", sa.Integer(), nullable=True))
    op.add_column("before_after_pairs", sa.Column("cleaning_type", sa.String(length=120), nullable=True))
    op.add_column("before_after_pairs", sa.Column("cleaners_count", sa.Integer(), nullable=True))
    op.add_column("before_after_pairs", sa.Column("duration_hours", sa.Numeric(4, 1), nullable=True))
    op.add_column("before_after_pairs", sa.Column("cost_text", sa.String(length=120), nullable=True))
    op.add_column("before_after_pairs", sa.Column("district", sa.String(length=160), nullable=True))
    op.add_column("before_after_pairs", sa.Column("task_text", sa.String(length=500), nullable=True))
    op.add_column("before_after_pairs", sa.Column("review_text", sa.String(length=500), nullable=True))

    # --- Отзывы: прозрачность (оригинал + вид уборки) ---
    op.add_column("reviews", sa.Column("source_url", sa.String(length=1024), nullable=True))
    op.add_column("reviews", sa.Column("service_type", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("reviews", "service_type")
    op.drop_column("reviews", "source_url")

    op.drop_column("before_after_pairs", "review_text")
    op.drop_column("before_after_pairs", "task_text")
    op.drop_column("before_after_pairs", "district")
    op.drop_column("before_after_pairs", "cost_text")
    op.drop_column("before_after_pairs", "duration_hours")
    op.drop_column("before_after_pairs", "cleaners_count")
    op.drop_column("before_after_pairs", "cleaning_type")
    op.drop_column("before_after_pairs", "area_sqm")
    op.drop_column("before_after_pairs", "room_type")

    op.drop_column("leads", "price")

    op.drop_column("addon_services", "max_qty")
    op.drop_column("addon_services", "unit")

    op.drop_column("services", "price_per_sqm")
