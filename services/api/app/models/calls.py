"""События звонков динамического коллтрекинга (Calltracking.ru).

Каждое уведомление вебхука сохраняется как CallEvent (идемпотентно по
external_id) и привязывается к автоматически созданному лиду — так звонок
попадает в CRM с UTM-метками, client_id Метрики и ссылкой на запись разговора.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CallEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "call_events"
    __table_args__ = (
        # Повторная доставка вебхука не создаёт дубликатов.
        UniqueConstraint("provider", "external_id", name="uq_call_provider_external"),
    )

    # calltracking (задел под другие провайдеры)
    provider: Mapped[str] = mapped_column(String(40), default="calltracking", nullable=False)
    external_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Номер звонящего и подменный (отслеживаемый) номер.
    caller_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    tracked_phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # answered | missed | busy | ... (как передал провайдер)
    status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    record_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    # Атрибуция сессии звонившего (передаёт коллтрекинг).
    utm: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ym_uid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    yclid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    gclid: Mapped[str | None] = mapped_column(String(128), nullable=True)
    site_domain: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Полный сырой payload вебхука — для отладки и доуточнения маппинга полей.
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Автосозданный лид (карточка звонка в CRM).
    lead_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("leads.id", ondelete="SET NULL"), nullable=True, index=True
    )
