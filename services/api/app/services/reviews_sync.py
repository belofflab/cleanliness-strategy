"""Агрегатор отзывов из внешних источников.

Архитектура: для каждого провайдера — свой коннектор с единым интерфейсом
fetch(place_id) -> list[ReviewItem]. Сейчас коннекторы возвращают
правдоподобные мок-данные (реальные API подключаются по ключам провайдера).
Синхронизация идемпотентна: upsert по (provider, external_id).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import reviews as reviews_repo

PROVIDER_YANDEX = "yandex"
PROVIDER_2GIS = "2gis"
PROVIDER_GOOGLE = "google"
SUPPORTED_PROVIDERS = (PROVIDER_YANDEX, PROVIDER_2GIS, PROVIDER_GOOGLE)


@dataclass
class ReviewItem:
    provider: str
    external_id: str
    author_name: str
    rating: float
    text: str
    published_at: datetime | None = None
    avatar_url: str | None = None


def dedup_items(items: list[ReviewItem]) -> list[ReviewItem]:
    """Убирает дубли по (provider, external_id), сохраняя порядок."""
    seen: set[tuple[str, str]] = set()
    result: list[ReviewItem] = []
    for item in items:
        key = (item.provider, item.external_id)
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


# --- Коннекторы провайдеров (мок). Реальные вызовут API по place_id и ключу. ---
def _mock_reviews(provider: str, place_id: str) -> list[ReviewItem]:
    now = datetime.now(timezone.utc)
    samples = {
        PROVIDER_YANDEX: ("Светлана", 5, "Бронировала через приложение — мастер приехал вовремя, всё блестит."),
        PROVIDER_2GIS: ("Артур", 5, "Удобный калькулятор, честная цена, аккуратная команда."),
        PROVIDER_GOOGLE: ("Юлия", 5, "Заказывала уборку после ремонта — идеально, рекомендую."),
    }
    author, rating, text = samples.get(provider, ("Гость", 5, "Отличный сервис."))
    return [
        ReviewItem(
            provider=provider,
            external_id=f"{place_id}:1",
            author_name=author,
            rating=float(rating),
            text=text,
            published_at=now - timedelta(days=2),
        )
    ]


def fetch_provider(provider: str, place_id: str) -> list[ReviewItem]:
    """Возвращает отзывы провайдера для конкретного place_id."""
    if provider not in SUPPORTED_PROVIDERS:
        return []
    # TODO: подключить реальные API (Яндекс/2ГИС/Google) по ключам провайдера.
    return _mock_reviews(provider, place_id)


async def sync_all(db: AsyncSession) -> tuple[int, int]:
    """Обходит активные источники и upsert-ит отзывы. Возвращает (создано, источников)."""
    sources = await reviews_repo.list_active_sources(db)
    created = 0
    for source in sources:
        items = dedup_items(fetch_provider(source.provider, source.external_place_id))
        for item in items:
            is_new = await reviews_repo.upsert_review(
                db,
                city_id=source.city_id,
                source_id=source.id,
                provider=item.provider,
                external_id=item.external_id,
                author_name=item.author_name,
                rating=item.rating,
                text=item.text,
                avatar_url=item.avatar_url,
                published_at=item.published_at,
            )
            if is_new:
                created += 1
    return created, len(sources)

