"""Общие зависимости FastAPI (Depends) для роутеров."""

from app.core.db import get_db

__all__ = ["get_db"]

