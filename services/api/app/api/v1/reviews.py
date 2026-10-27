"""Публичные и админские эндпоинты отзывов."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import require_roles
from app.api.deps import get_db
from app.models.auth import ROLE_ADMIN, ROLE_MANAGER, User
from app.repositories import catalog as catalog_repo
from app.repositories import reviews as reviews_repo
from app.schemas.reviews import ReviewCreate, ReviewOut, ReviewSyncResult
from app.services.reviews_sync import sync_all

router = APIRouter(tags=["reviews"])


async def _city_id(db: AsyncSession, city_slug: str | None):
    if not city_slug:
        return None
    city = await catalog_repo.get_active_city_by_slug(db, city_slug)
    return city.id if city else None


@router.get("/reviews", response_model=list[ReviewOut])
async def list_reviews(
    city_slug: str | None = Query(None),
    limit: int = Query(30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Публичный список опубликованных отзывов (для слайдера на сайте)."""
    city_id = await _city_id(db, city_slug)
    reviews = await reviews_repo.list_published(db, city_id=city_id, limit=limit)
    return [
        ReviewOut(
            id=str(r.id),
            author_name=r.author_name,
            rating=float(r.rating),
            text=r.text,
            provider=r.provider,
            avatar_url=r.avatar_url,
            source_url=r.source_url,
            service_type=r.service_type,
            published_at=r.published_at,
        )
        for r in reviews
    ]


@router.post("/admin/reviews", response_model=ReviewOut, tags=["admin"])
async def create_review(
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_MANAGER)),
):
    """Ручное добавление отзыва (модерация/витрина) — менеджер/админ."""
    city_id = await _city_id(db, payload.city_slug)
    await reviews_repo.upsert_review(
        db,
        city_id=city_id,
        source_id=None,
        provider="manual",
        external_id=None,
        author_name=payload.author_name,
        rating=payload.rating,
        text=payload.text,
        avatar_url=payload.avatar_url,
        published_at=None,
    )
    # Возвращаем посл��дний созданный (упрощённо — перечитываем список).
    latest = await reviews_repo.list_published(db, city_id=city_id, limit=1)
    r = latest[0]
    return ReviewOut(
        id=str(r.id), author_name=r.author_name, rating=float(r.rating),
        text=r.text, provider=r.provider, avatar_url=r.avatar_url, published_at=r.published_at,
    )


@router.post("/admin/reviews/sync", response_model=ReviewSyncResult, tags=["admin"])
async def trigger_sync(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_MANAGER)),
):
    """Ручной запуск синхронизации отзывов из внешних источников."""
    created, sources = await sync_all(db)
    return ReviewSyncResult(synced=created, sources=sources)

