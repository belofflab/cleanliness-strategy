"""Доступ к данным отзывов и источников."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.reviews import Review, ReviewSource


async def list_published(
    db: AsyncSession, *, city_id: uuid.UUID | None = None, limit: int = 30
) -> list[Review]:
    stmt = select(Review).where(Review.is_published.is_(True))
    if city_id is not None:
        stmt = stmt.where((Review.city_id == city_id) | (Review.city_id.is_(None)))
    stmt = stmt.order_by(Review.published_at.desc().nullslast()).limit(limit)
    return list((await db.execute(stmt)).scalars().all())


async def list_active_sources(db: AsyncSession) -> list[ReviewSource]:
    stmt = select(ReviewSource).where(ReviewSource.is_active.is_(True))
    return list((await db.execute(stmt)).scalars().all())


async def get_by_external(db: AsyncSession, *, provider: str, external_id: str) -> Review | None:
    stmt = select(Review).where(
        Review.provider == provider, Review.external_id == external_id
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def upsert_review(
    db: AsyncSession,
    *,
    city_id: uuid.UUID | None,
    source_id: uuid.UUID | None,
    provider: str,
    external_id: str | None,
    author_name: str,
    rating: float,
    text: str,
    avatar_url: str | None,
    published_at: datetime | None,
) -> bool:
    """Идемпотентный upsert по (provider, external_id). True — если создан новый."""
    if external_id is not None:
        existing = await get_by_external(db, provider=provider, external_id=external_id)
        if existing is not None:
            existing.author_name = author_name
            existing.rating = rating
            existing.text = text
            existing.avatar_url = avatar_url
            existing.published_at = published_at
            await db.commit()
            return False

    review = Review(
        city_id=city_id,
        source_id=source_id,
        provider=provider,
        external_id=external_id,
        author_name=author_name,
        rating=rating,
        text=text,
        avatar_url=avatar_url,
        published_at=published_at,
        is_published=True,
    )
    db.add(review)
    await db.commit()
    return True

