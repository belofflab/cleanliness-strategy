"""Медиа и блок «До/После»: публичный показ + админская загрузка."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth_deps import require_roles
from app.api.city_context import resolve_city
from app.api.deps import get_db
from app.core.config import get_settings
from app.models.auth import ROLE_ADMIN, ROLE_MANAGER, User
from app.models.catalog import City
from app.repositories import catalog as catalog_repo
from app.repositories import media as media_repo
from app.schemas.content import (
    ContentAddonOut,
    ContentBranchOut,
    ContentCityOut,
    ContentResponse,
    ContentSeoOut,
    ContentServiceOut,
)
from app.schemas.media import (
    BeforeAfterCreate,
    BeforeAfterOut,
    MediaOut,
    PresignRequest,
    PresignResponse,
)
from app.services.media import MediaError, presign_upload, upload_bytes

router = APIRouter(tags=["media"])


def _city_origin(slug: str) -> str:
    """Канонический origin города: город по умолчанию живёт на apex-домене."""
    settings = get_settings()
    if slug == settings.default_city_slug:
        return f"https://{settings.public_base_domain}"
    return f"https://{slug}.{settings.public_base_domain}"


@router.get("/content", response_model=ContentResponse, tags=["content"])
async def get_content(
    request: Request,
    city: City = Depends(resolve_city),
    db: AsyncSession = Depends(get_db),
):
    """Публичный city-aware контент для лендинга: контакты, каталог, SEO."""
    services = await catalog_repo.list_services(db, city.id)
    addons = await catalog_repo.list_addons(db, city.id)
    branches = await catalog_repo.list_branches(db, city.id)
    active_cities = await catalog_repo.list_active_cities(db)

    current_origin = _city_origin(city.slug)
    path = request.url.path or "/"

    hreflang = {
        f"ru-RU-{alt_city.slug}": f"{_city_origin(alt_city.slug)}{path}"
        for alt_city in active_cities
    }
    hreflang["x-default"] = f"{_city_origin(get_settings().default_city_slug)}{path}"

    seo = ContentSeoOut(
        title=f"Точка Чистоты — Премиальный клининг {city.name_prepositional}",
        description=(
            f"Премиальный клининг квартир, домов и офисов {city.name_prepositional}. "
            "Прозрачная цена, быстрый выезд и контроль качества на каждом этапе."
        ),
        canonical=f"{current_origin}{path}",
        hreflang=hreflang,
    )

    return ContentResponse(
        city=ContentCityOut(
            slug=city.slug,
            name=city.name,
            name_prepositional=city.name_prepositional,
            timezone=city.timezone,
            phone=city.phone,
            email=city.email,
        ),
        services=[
            ContentServiceOut(
                type=service.type,
                name=service.name,
                base_price=float(service.base_price),
                price_per_room=float(service.price_per_room),
                price_per_bathroom=float(service.price_per_bathroom),
                price_per_sqm=float(service.price_per_sqm or 0),
                minutes_base=service.minutes_base,
                minutes_per_room=service.minutes_per_room,
                minutes_per_bathroom=service.minutes_per_bathroom,
            )
            for service in services
        ],
        addons=[
            ContentAddonOut(
                code=addon.code,
                name=addon.name,
                price=float(addon.price),
                minutes=addon.minutes,
                unit=addon.unit,
                max_qty=addon.max_qty,
            )
            for addon in addons
        ],
        branches=[
            ContentBranchOut(
                name=branch.name,
                address=branch.address,
                phone=branch.phone,
                email=branch.email,
                working_hours=branch.working_hours,
            )
            for branch in branches
        ],
        seo=seo,
    )


@router.get("/before-after", response_model=list[BeforeAfterOut])
async def list_before_after(
    city_slug: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Публичные пары «До/После» (для одноимённого блока сайта)."""
    city_id = None
    if city_slug:
        city = await catalog_repo.get_active_city_by_slug(db, city_slug)
        city_id = city.id if city else None

    pairs = await media_repo.list_before_after(db, city_id)
    result: list[BeforeAfterOut] = []
    for pair in pairs:
        before = await media_repo.get_media(db, pair.before_media_id)
        after = await media_repo.get_media(db, pair.after_media_id)
        if before and after:
            result.append(
                BeforeAfterOut(
                    id=str(pair.id), title=pair.title,
                    before_url=before.url, after_url=after.url,
                    room_type=pair.room_type,
                    area_sqm=pair.area_sqm,
                    cleaning_type=pair.cleaning_type,
                    cleaners_count=pair.cleaners_count,
                    duration_hours=float(pair.duration_hours) if pair.duration_hours is not None else None,
                    cost_text=pair.cost_text,
                    district=pair.district,
                    task_text=pair.task_text,
                    review_text=pair.review_text,
                )
            )
    return result


@router.post("/admin/media/upload", response_model=MediaOut, tags=["admin"])
async def upload_media(
    file: UploadFile = File(...),
    owner_type: str = Form("other"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_MANAGER)),
):
    """Загрузка файла в S3 (аватар мастера, фото «До/После») — менеджер/админ."""
    try:
        media = await upload_bytes(
            db,
            data=file.file,
            filename=file.filename or "upload.bin",
            content_type=file.content_type,
            owner_type=owner_type,
        )
    except MediaError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    return MediaOut(id=str(media.id), url=media.url, content_type=media.content_type)


@router.post("/admin/media/presign", response_model=PresignResponse, tags=["admin"])
async def presign(
    payload: PresignRequest,
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_MANAGER)),
):
    """Presigned-URL для прямой загрузки файла клиентом."""
    try:
        data = presign_upload(
            owner_type=payload.owner_type,
            filename=payload.filename,
            content_type=payload.content_type,
        )
    except MediaError as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=exc.message) from exc
    return PresignResponse(**data)


@router.post("/admin/before-after", response_model=BeforeAfterOut, tags=["admin"])
async def create_before_after(
    payload: BeforeAfterCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_roles(ROLE_ADMIN, ROLE_MANAGER)),
):
    """Создать пару «До/После» из загруженных медиа."""
    city_id = None
    if payload.city_slug:
        city = await catalog_repo.get_active_city_by_slug(db, payload.city_slug)
        city_id = city.id if city else None

    pair = await media_repo.create_before_after(
        db,
        city_id=city_id,
        title=payload.title,
        before_media_id=uuid.UUID(payload.before_media_id),
        after_media_id=uuid.UUID(payload.after_media_id),
        sort_order=payload.sort_order,
    )
    before = await media_repo.get_media(db, pair.before_media_id)
    after = await media_repo.get_media(db, pair.after_media_id)
    return BeforeAfterOut(
        id=str(pair.id), title=pair.title,
        before_url=before.url if before else "",
        after_url=after.url if after else "",
    )

