"""normalize lead phones: единый формат +7XXXXXXXXXX (дефект R1 аудита)

Лиды с сайта и букинга сохранялись в формате ввода («+7 (917) 000-00-00»),
а учётки пользователей — нормализованными («+79170000000»). Заказы клиента
ищутся по совпадению телефона лида и учётки, поэтому клиент не видел свои
заказы в мобайле, а уведомления о статусе не создавались.

Приводим существующие записи к формату normalize_phone() (см.
app/services/phones.py): оставляем только цифры, «8XXXXXXXXXX» → «7XXXXXXXXXX»,
добавляем «+». Новые лиды нормализует репозиторий при создании.

Revision ID: 0010_normalize_lead_phones
Revises: 0009_fix_call_events
Create Date: 2026-09-11
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0010_normalize_lead_phones"
down_revision: Union[str, None] = "0009_fix_call_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_NORMALIZED = (
    "'+' || CASE WHEN src.digits ~ '^8[0-9]{10}$' "
    "THEN '7' || substr(src.digits, 2) ELSE src.digits END"
)


def upgrade() -> None:
    op.execute(
        f"""
        UPDATE leads AS l
        SET phone = {_NORMALIZED}
        FROM (
            SELECT id, regexp_replace(phone, '[^0-9]', '', 'g') AS digits
            FROM leads
        ) AS src
        WHERE l.id = src.id
          AND src.digits <> ''
          AND l.phone IS DISTINCT FROM ({_NORMALIZED})
        """
    )


def downgrade() -> None:
    # Исходное форматирование восстановить нельзя; нормализованный формат
    # валиден для всех потребителей (админка форматирует при показе).
    pass
