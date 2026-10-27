"""Доступ к данным медиа и пар «До/После»."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.media import BeforeAfterPair, Media


async def create_media(
    db: AsyncSession,
    *,
    owner_type: str,
    owner_id: uuid.UUID | None,
    bucket: str,
    key: str,
    url: str,
    content_type: str | None,
) -> Media:
    media = Media(
        owner_type=owner_type,
        owner_id=owner_id,
        bucket=bucket,
        key=key,
        url=url,
        content_type=content_type,
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)
    return media


async def get_media(db: AsyncSession, media_id: uuid.UUID) -> Media | None:
    return await db.get(Media, media_id)


async def list_before_after(db: AsyncSession, city_id: uuid.UUID | None) -> list[BeforeAfterPair]:
    stmt = select(BeforeAfterPair).where(BeforeAfterPair.is_active.is_(True))
    if city_id is not None:
        stmt = stmt.where(
            (BeforeAfterPair.city_id == city_id) | (BeforeAfterPair.city_id.is_(None))
        )
    stmt = stmt.order_by(BeforeAfterPair.sort_order)
    return list((await db.execute(stmt)).scalars().all())


async def create_before_after(
    db: AsyncSession,
    *,
    city_id: uuid.UUID | None,
    title: str | None,
    before_media_id: uuid.UUID,
    after_media_id: uuid.UUID,
    sort_order: int,
) -> BeforeAfterPair:
    pair = BeforeAfterPair(
        city_id=city_id,
        title=title,
        before_media_id=before_media_id,
        after_media_id=after_media_id,
        sort_order=sort_order,
        is_active=True,
    )
    db.add(pair)
    await db.commit()
    await db.refresh(pair)
    return pair

