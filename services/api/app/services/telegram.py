"""Мгновенное уведомление операторов о новом лиде через Telegram (Этап 3.3).

Цель — реакция оператора за 1–2 минуты: как только лид сохранён, в рабочий
чат прилетает сообщение с контактом и контекстом заявки. Доставка идёт фоном
(BackgroundTasks/Celery), поэтому ответ пользователю остаётся мгновенным.

Без токена/чата (TELEGRAM_ENABLED=false) работает mock-режим: ничего не
отправляется, сервис не падает — удобно для локальной разработки.
"""

from __future__ import annotations

import html
import uuid

import httpx
from loguru import logger

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.repositories import leads as leads_repo

_API_TEMPLATE = "https://api.telegram.org/bot{token}/sendMessage"


async def send_message(text: str) -> bool:
    """Отправляет сообщение в операторский чат. Возвращает True при успехе."""
    settings = get_settings()
    if not (
        settings.telegram_enabled
        and settings.telegram_bot_token
        and settings.telegram_chat_id
    ):
        logger.bind(channel="telegram", mocked=True).info("telegram_skip")
        return False

    url = _API_TEMPLATE.format(token=settings.telegram_bot_token)
    payload = {
        "chat_id": settings.telegram_chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json=payload)
        ok = response.status_code == 200
        logger.bind(channel="telegram", status=response.status_code).info(
            "telegram_sent" if ok else "telegram_failed"
        )
        return ok
    except Exception as exc:  # noqa: BLE001 — сеть/таймаут не должны ронять заявку
        logger.bind(channel="telegram").warning(f"telegram_error: {exc}")
        return False


def _format_lead(lead) -> str:
    """HTML-сообщение оператору. Телефон кликабелен для быстрого звонка."""
    city = lead.city.name if lead.city else "—"
    name = html.escape(lead.name or "—")
    phone = html.escape(lead.phone or "—")
    source = html.escape(lead.source or "—")
    context = html.escape(lead.context or "")
    lines = [
        "🆕 <b>Новый лид — Точка Чистоты</b>",
        f"👤 Имя: <b>{name}</b>",
        f"📞 Телефон: <a href=\"tel:{phone}\">{phone}</a>",
        f"🏙 Город: {html.escape(city)}",
        f"🔗 Источник: {source}",
    ]
    if context:
        lines.append(f"📝 {context}")
    lines.append("\n⏱ Перезвоните в течение 1–2 минут.")
    return "\n".join(lines)


async def notify_new_lead(lead_id: uuid.UUID) -> None:
    """Фоновая задача: грузит лид и шлёт уведомление операторам.

    Открывает собственную сессию БД (сессия запроса уже закрыта).
    """
    async with AsyncSessionLocal() as db:
        lead = await leads_repo.get_lead(db, lead_id)
    if lead is None:
        return
    await send_message(_format_lead(lead))
