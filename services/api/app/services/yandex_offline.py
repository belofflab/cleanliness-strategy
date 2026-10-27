"""Офлайн-конверсии в Яндекс.Метрику (обучение автостратегий Директа).

Когда заказ доводится до статуса «done» («Клининг выполнен»), отправляем
конверсию в Метрику через Management API:
POST /management/v1/counter/{id}/offline_conversions/upload

Идентификатор посетителя — ClientId Метрики (_ym_uid лида) либо yclid клика
Директа. Цели офлайн-конверсий импортируются в Директ автоматически, поэтому
отдельная интеграция с API Директа не нужна: автостратегии учатся на этих
данных через связку счётчика с рекламным кабинетом.

Без YANDEX_METRIKA_TOKEN работает mock-режим (логируем и выходим) — сервис
не падает и не шлёт ничего наружу.
"""

from __future__ import annotations

import logging
import time
import uuid

import httpx

from app.core.config import get_settings
from app.core.db import AsyncSessionLocal
from app.modules.orders import repository as orders_repo

logger = logging.getLogger(__name__)

METRIKA_API_BASE = "https://api-metrika.yandex.net"


def build_conversion_csv(
    *,
    target: str,
    ym_uid: str | None,
    yclid: str | None,
    price: float | None,
    timestamp: int | None = None,
) -> tuple[str, str] | None:
    """Чистая сборка CSV офлайн-конверсии.

    Возвращает (client_id_type, csv_text) либо None, если посетителя
    не с чем связать (нет ни ClientId Метрики, ни yclid).
    """
    ts = timestamp or int(time.time())
    price_part = f",{price:.2f},RUB" if price is not None else ",,"

    if ym_uid:
        header = "ClientId,Target,DateTime,Price,Currency"
        row = f"{ym_uid},{target},{ts}{price_part}"
        return "CLIENT_ID", f"{header}\n{row}\n"

    if yclid:
        header = "Yclid,Target,DateTime,Price,Currency"
        row = f"{yclid},{target},{ts}{price_part}"
        return "YCLID", f"{header}\n{row}\n"

    return None


async def upload_conversion(
    *,
    target: str,
    ym_uid: str | None,
    yclid: str | None,
    price: float | None,
) -> dict:
    """Отправляет одну офлайн-конверсию в Метрику. Mock-режим без токена."""
    settings = get_settings()

    built = build_conversion_csv(target=target, ym_uid=ym_uid, yclid=yclid, price=price)
    if built is None:
        logger.info("Офлайн-конверсия пропущена: у лида нет ym_uid/yclid")
        return {"status": "skipped", "reason": "no_client_identifier"}

    client_id_type, csv_text = built

    if not settings.yandex_metrika_token:
        logger.info(
            "Офлайн-конверсия (mock, нет YANDEX_METRIKA_TOKEN): %s", csv_text.strip()
        )
        return {"status": "mocked", "csv": csv_text, "client_id_type": client_id_type}

    url = (
        f"{METRIKA_API_BASE}/management/v1/counter/"
        f"{settings.yandex_metrika_counter_id}/offline_conversions/upload"
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                url,
                params={"client_id_type": client_id_type},
                headers={"Authorization": f"OAuth {settings.yandex_metrika_token}"},
                files={"file": ("conversions.csv", csv_text, "text/csv")},
            )
        body: dict | str
        try:
            body = response.json()
        except ValueError:
            body = response.text[:500]
        if response.is_success:
            logger.info("Офлайн-конверсия загружена в Метрику: %s", body)
            return {"status": "uploaded", "response": body}
        logger.error("Метрика ответила ошибкой на офлайн-конверсию: %s %s", response.status_code, body)
        return {"status": "error", "http_status": response.status_code, "response": body}
    except Exception as exc:  # noqa: BLE001 — сеть не должна ронять смену статуса
        logger.error("Не удалось отправить офлайн-конверсию: %s", exc)
        return {"status": "error", "error": str(exc)}


async def upload_order_done_conversion(order_id: uuid.UUID | str) -> dict:
    """Конверсия «Клининг выполнен» по заказу: открывает собственную сессию БД."""
    settings = get_settings()
    order_uuid = uuid.UUID(str(order_id))

    async with AsyncSessionLocal() as db:
        order = await orders_repo.get_order(db, order_uuid)
        if order is None:
            return {"status": "skipped", "reason": "order_not_found"}
        lead = order.lead
        ym_uid = lead.ym_uid if lead else None
        yclid = lead.yclid if lead else None
        price = float(order.total_price) if order.total_price is not None else None

    return await upload_conversion(
        target=settings.yandex_metrika_goal_done,
        ym_uid=ym_uid,
        yclid=yclid,
        price=price,
    )
