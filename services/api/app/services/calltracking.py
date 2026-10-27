"""Приём звонков от Calltracking.ru (Webhook API) → лид в собственной CRM.

Провайдеры коллтрекинга отличаются именами полей в уведомлениях, поэтому
парсер терпимый: принимает JSON/form/query, ищет значения по списку синонимов
и всегда сохраняет сырой payload в call_events.raw_payload — если кабинет
Calltracking пришлёт поле под другим именем, его видно в БД и маппинг легко
дополнить здесь.

Дизайн повторяет пайплайн лидов с сайта: событие звонка сохраняется ВСЕГДА,
лид создаётся идемпотентно (дедуп по номеру в окне), операторов пингует
Telegram — фоном, из роутера.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.calls import CallEvent
from app.models.orders import Lead
from app.repositories import catalog as catalog_repo
from app.repositories import leads as leads_repo
from app.services.city_resolution import extract_city_slug_from_host
from app.services.phones import normalize_phone

logger = logging.getLogger(__name__)

# Окно дедупликации лидов по звонку: повторный вебхук/перезвон того же номера
# в этом окне НЕ создаёт второй лид (событие звонка сохраняется всегда).
LEAD_DEDUP_WINDOW_MINUTES = 30

# Синонимы полей уведомления (разные провайдеры/версии кабинета).
_FIELD_SYNONYMS: dict[str, tuple[str, ...]] = {
    "external_id": ("id", "call_id", "callid", "uid", "call_uid", "notification_id"),
    "caller_phone": (
        "phone", "caller", "caller_number", "client_phone", "client_number",
        "numb", "src", "from", "phone_client",
    ),
    "tracked_phone": (
        "called", "called_number", "dst", "to", "virtual_number", "number",
        "tracking_number", "phone_virtual", "site_phone",
    ),
    "duration": ("duration", "talk_time", "call_duration", "duration_sec", "billsec"),
    "status": ("status", "call_status", "type", "result", "disposition"),
    "record_url": (
        "record", "record_url", "record_link", "link_record", "url_record",
        "recording", "recording_url", "record_file",
    ),
    "ym_uid": ("ym_uid", "_ym_uid", "ym_client_id", "yandex_client_id", "clientid", "client_id"),
    "yclid": ("yclid",),
    "gclid": ("gclid",),
    "site_domain": ("site", "domain", "hostname", "site_domain", "host"),
    "utm_source": ("utm_source",),
    "utm_medium": ("utm_medium",),
    "utm_campaign": ("utm_campaign",),
    "utm_content": ("utm_content",),
    "utm_term": ("utm_term",),
}


@dataclass
class CallData:
    """Нормализованные данные звонка (независимы от формата вебхука)."""

    caller_phone: str
    external_id: str | None = None
    tracked_phone: str | None = None
    duration_seconds: int | None = None
    status: str | None = None
    record_url: str | None = None
    utm: dict = field(default_factory=dict)
    ym_uid: str | None = None
    yclid: str | None = None
    gclid: str | None = None
    site_domain: str | None = None
    raw: dict = field(default_factory=dict)


class CallWebhookError(DomainError):
    status_code = 422
    code = "call_webhook_error"


def _pick(payload: dict, key: str) -> str | None:
    """Достаёт значение по списку синонимов (без учёта регистра ключей)."""
    lowered = {str(k).lower(): v for k, v in payload.items()}
    for name in _FIELD_SYNONYMS[key]:
        value = lowered.get(name)
        if value is not None and str(value).strip() not in ("", "null", "None"):
            return str(value).strip()
    return None


def parse_call_payload(payload: dict) -> CallData:
    """Чистая нормализация payload вебхука → CallData (легко тестируется)."""
    caller = _pick(payload, "caller_phone")
    if not caller:
        raise CallWebhookError("В уведомлении нет номера звонящего (phone/caller)")

    # UTM: плоские ключи либо вложенный dict "utm".
    utm: dict = {}
    nested_utm = payload.get("utm")
    if isinstance(nested_utm, dict):
        utm.update({k: str(v) for k, v in nested_utm.items() if v})
    for utm_key in ("source", "medium", "campaign", "content", "term"):
        value = _pick(payload, f"utm_{utm_key}")
        if value:
            utm[utm_key] = value

    duration_raw = _pick(payload, "duration")
    try:
        duration = int(float(duration_raw)) if duration_raw else None
    except ValueError:
        duration = None

    return CallData(
        caller_phone=normalize_phone(caller),
        external_id=_pick(payload, "external_id"),
        tracked_phone=normalize_phone(_pick(payload, "tracked_phone") or "") or None,
        duration_seconds=duration,
        status=_pick(payload, "status"),
        record_url=_pick(payload, "record_url"),
        utm=utm,
        ym_uid=_pick(payload, "ym_uid"),
        yclid=_pick(payload, "yclid"),
        gclid=_pick(payload, "gclid"),
        site_domain=_pick(payload, "site_domain"),
        raw=payload,
    )


def resolve_city_slug(call: CallData) -> str:
    """Определяет город звонка: карта подменных номеров → домен → дефолт."""
    settings = get_settings()

    if call.tracked_phone and settings.calltracking_city_numbers:
        try:
            number_map = json.loads(settings.calltracking_city_numbers)
            mapped = {normalize_phone(k): v for k, v in number_map.items()}
            if call.tracked_phone in mapped:
                return mapped[call.tracked_phone]
        except (ValueError, AttributeError) as exc:
            logger.warning("CALLTRACKING_CITY_NUMBERS не парсится как JSON: %s", exc)

    # Поддомен сайта → город (ufa.<base_domain> → ufa); apex/неизвестный → город по умолчанию.
    slug = extract_city_slug_from_host(call.site_domain, settings.public_base_domain)
    return slug or settings.default_city_slug


def build_call_context(call: CallData) -> str:
    """Текст карточки лида: менеджер видит суть звонка сразу."""
    parts = ["Входящий звонок (Calltracking)"]
    if call.status:
        parts.append(f"статус: {call.status}")
    if call.duration_seconds is not None:
        minutes, seconds = divmod(call.duration_seconds, 60)
        parts.append(f"длительность: {minutes:02d}:{seconds:02d}")
    if call.tracked_phone:
        parts.append(f"подменный номер: {call.tracked_phone}")
    if call.record_url:
        parts.append(f"запись разговора: {call.record_url}")
    return " | ".join(parts)


async def process_call_event(db: AsyncSession, payload: dict) -> dict:
    """Сохраняет событие звонка и создаёт лид (идемпотентно).

    Возвращает словарь для ответа вебхуку: {status, call_event_id, lead_id}.
    Отправку лида в CRM планирует ВЫЗЫВАЮЩИЙ код (роутер) — там есть
    BackgroundTasks; здесь только БД-работа.
    """
    call = parse_call_payload(payload)

    # 1. Идемпотентность по external_id: повторная доставка — не дубликат.
    if call.external_id:
        existing = (
            await db.execute(
                select(CallEvent).where(
                    CallEvent.provider == "calltracking",
                    CallEvent.external_id == call.external_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return {
                "status": "duplicate",
                "call_event_id": str(existing.id),
                "lead_id": str(existing.lead_id) if existing.lead_id else None,
            }

    city_slug = resolve_city_slug(call)
    city = await catalog_repo.get_active_city_by_slug(db, city_slug)

    # 2. Дедупликация лида: недавний звонок с того же номера не плодит карточки.
    dedup_after = datetime.now(timezone.utc) - timedelta(minutes=LEAD_DEDUP_WINDOW_MINUTES)
    recent_lead = (
        await db.execute(
            select(Lead)
            .where(
                Lead.source == "call",
                Lead.phone == call.caller_phone,
                Lead.created_at >= dedup_after,
            )
            .order_by(Lead.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    lead = recent_lead
    lead_created = False
    if lead is None:
        lead = await leads_repo.create_lead(
            db,
            name="Входящий звонок",
            phone=call.caller_phone,
            source="call",
            context=build_call_context(call),
            utm=call.utm or None,
            yclid=call.yclid,
            ym_uid=call.ym_uid,
            gclid=call.gclid,
            city_id=city.id if city else None,
        )
        lead_created = True

    # 3. Событие звонка сохраняется всегда (в т.ч. для повторных звонков).
    event = CallEvent(
        provider="calltracking",
        external_id=call.external_id,
        caller_phone=call.caller_phone,
        tracked_phone=call.tracked_phone,
        duration_seconds=call.duration_seconds,
        status=call.status,
        record_url=call.record_url,
        utm=call.utm or None,
        ym_uid=call.ym_uid,
        yclid=call.yclid,
        gclid=call.gclid,
        site_domain=call.site_domain,
        raw_payload=call.raw,
        lead_id=lead.id,
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)

    return {
        "status": "created",
        "call_event_id": str(event.id),
        "lead_id": str(lead.id),
        "lead_created": lead_created,
    }
