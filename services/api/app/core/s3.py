"""S3-клиент для Yandex Object Storage (boto3, S3-совместимый API).

Документация: https://yandex.cloud/ru/docs/storage/s3/
Без ключей (S3_ENABLED=false) методы возвращают None — сервис не падает.
Ключи берутся ТОЛЬКО из окружения, в коде их быть не должно.
"""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import BinaryIO

import boto3
from botocore.config import Config

from app.core.config import get_settings


@lru_cache
def _client():
    settings = get_settings()
    if not settings.s3_enabled:
        return None
    return boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        region_name=settings.s3_region,
        aws_access_key_id=settings.s3_access_key_id,
        aws_secret_access_key=settings.s3_secret_access_key,
        config=Config(signature_version="s3v4"),
    )


def build_key(prefix: str, filename: str) -> str:
    """Уникальный ключ объекта: prefix/uuid-filename."""
    safe = filename.replace("/", "_").strip()
    return f"{prefix.strip('/')}/{uuid.uuid4().hex}-{safe}"


def public_url(key: str) -> str:
    """Публичный URL объекта для отдачи во фронтенд."""
    settings = get_settings()
    base = settings.s3_public_base_url.rstrip("/")
    if base:
        return f"{base}/{key}"
    return f"{settings.s3_endpoint_url.rstrip('/')}/{settings.s3_bucket}/{key}"


def upload_fileobj(
    fileobj: BinaryIO, key: str, content_type: str | None = None
) -> str | None:
    """Загружает объект в бакет, возвращает публичный URL (или None в mock)."""
    client = _client()
    settings = get_settings()
    if client is None:
        return None
    extra = {"ContentType": content_type} if content_type else {}
    client.upload_fileobj(fileobj, settings.s3_bucket, key, ExtraArgs=extra)
    return public_url(key)


def presigned_put(key: str, expires: int = 3600, content_type: str | None = None) -> str | None:
    """Presigned-URL для прямой загрузки с клиента (мобилка/админка)."""
    client = _client()
    settings = get_settings()
    if client is None:
        return None
    params = {"Bucket": settings.s3_bucket, "Key": key}
    if content_type:
        params["ContentType"] = content_type
    return client.generate_presigned_url("put_object", Params=params, ExpiresIn=expires)

