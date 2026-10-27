"""Интеграционный тест приёма лида в собственную CRM (требует PostgreSQL).

Внешней CRM нет: лид сохраняется со статусом new, менеджер работает с ним
в админке (воронка new → in_progress → converted/rejected).
"""

from __future__ import annotations

import pytest

from app.models.orders import LEAD_IN_PROGRESS, LEAD_NEW
from app.repositories import leads as leads_repo

pytestmark = pytest.mark.asyncio


async def test_lead_persisted_with_new_status(db_session):
    lead = await leads_repo.create_lead(
        db_session,
        name="Интеграционный тест",
        phone="+79170000000",
        source="quiz",
        context="Квиз-заявка → тест",
        utm={"source": "yandexpoisk", "campaign": "test"},
        yclid="y-1",
        ym_uid="ym-1",
        city_id=None,
        price=5000,
        gclid="g-1",
        service_type="Генеральная",
    )
    assert lead.status == LEAD_NEW
    assert lead.utm["source"] == "yandexpoisk"
    assert lead.gclid == "g-1"
    assert float(lead.price) == 5000


async def test_lead_card_update_and_validation(db_session):
    lead = await leads_repo.create_lead(
        db_session,
        name="Карточка",
        phone="+79170000001",
        source="callback",
        context=None,
        utm=None,
        yclid=None,
        ym_uid=None,
        city_id=None,
    )

    updated = await leads_repo.update_lead_card(
        db_session, lead, status=LEAD_IN_PROGRESS, manager_note="Перезвонить после 18:00"
    )
    assert updated.status == LEAD_IN_PROGRESS
    assert updated.manager_note == "Перезвонить после 18:00"

    with pytest.raises(ValueError):
        await leads_repo.update_lead_card(db_session, lead, status="sent_to_crm")
