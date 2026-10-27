"""Отправка SMS через sms.ru с безопасным mock-режимом.

Документация: https://sms.ru/api/send
Без ключа (SMS_ENABLED=false) сообщение не отправляется реально —
в dev код возвращается в ответе API для удобства тестирования.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.config import get_settings


@dataclass
class SmsResult:
    sent: bool
    mocked: bool = False
    error: str | None = None


async def send_sms(phone: str, text: str) -> SmsResult:
    settings = get_settings()

    # Mock-режим: ключ не задан — реальной отправки нет.
    if not (settings.sms_enabled and settings.sms_ru_api_id):
        return SmsResult(sent=True, mocked=True)

    params = {
        "api_id": settings.sms_ru_api_id,
        "to": phone.lstrip("+"),
        "msg": text,
        "json": 1,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get("https://sms.ru/sms/send", params=params)
        data = response.json()
        ok = data.get("status") == "OK"
        return SmsResult(sent=ok, error=None if ok else str(data))
    except Exception as exc:  # noqa: BLE001
        return SmsResult(sent=False, error=str(exc))

