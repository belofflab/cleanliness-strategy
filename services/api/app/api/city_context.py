"""Определение активного города из контекста запроса."""

from __future__ import annotations

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.config import get_settings
from app.models.catalog import City
from app.repositories import catalog as catalog_repo
from app.services.city_resolution import extract_city_slug_from_host


async def resolve_city(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> City:
    """Приоритет: Host subdomain -> X-City-Slug -> город по умолчанию (DEFAULT_CITY_SLUG)."""
    settings = get_settings()

    host_slug = extract_city_slug_from_host(
        request.headers.get("host"), settings.public_base_domain
    )
    if host_slug:
        city = await catalog_repo.get_active_city_by_slug(db, host_slug)
        if city is not None:
            return city

    header_slug = request.headers.get("x-city-slug", "").strip().lower()
    if header_slug:
        city = await catalog_repo.get_active_city_by_slug(db, header_slug)
        if city is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Город '{header_slug}' не найден",
            )
        return city

    default_city = await catalog_repo.get_active_city_by_slug(db, settings.default_city_slug)
    if default_city is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Город по умолчанию не настроен",
        )
    return default_city
