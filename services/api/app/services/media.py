"""Сервис загрузки медиа в S3 (Yandex Object Storage) + запись в БД."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import s3
from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.media import Media
from app.repositories import media as media_repo


class MediaError(DomainError):
    status_code = 503
    code = "media_error"


async def upload_bytes(
    db: AsyncSession,
    *,
    data,
    filename: str,
    content_type: str | None,
    owner_type: str,
    owner_id: uuid.UUID | None = None,
) -> Media:
    """Загружает файловый объект в S3 и сохраняет запись Media."""
    settings = get_settings()
    if not settings.s3_enabled:
        raise MediaError("S3 не настроен (S3_ENABLED=false)")

    key = s3.build_key(prefix=owner_type, filename=filename)
    url = s3.upload_fileobj(data, key, content_type=content_type)
    if url is None:
        raise MediaError("Не удалось загрузить файл в S3")

    return await media_repo.create_media(
        db,
        owner_type=owner_type,
        owner_id=owner_id,
        bucket=settings.s3_bucket,
        key=key,
        url=url,
        content_type=content_type,
    )


def presign_upload(*, owner_type: str, filename: str, content_type: str | None) -> dict:
    """Готовит presigned-URL для прямой загрузки с клиента (мобилка/админка)."""
    settings = get_settings()
    if not settings.s3_enabled:
        raise MediaError("S3 не настроен (S3_ENABLED=false)")

    key = s3.build_key(prefix=owner_type, filename=filename)
    upload_url = s3.presigned_put(key, content_type=content_type)
    if upload_url is None:
        raise MediaError("Не удалось создать presigned-URL")
    return {"key": key, "upload_url": upload_url, "public_url": s3.public_url(key)}

