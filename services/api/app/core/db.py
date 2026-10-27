"""Подключение к PostgreSQL через async SQLAlchemy 2.0.

Здесь создаём engine, фабрику сессий и базовый класс моделей.
Сессия выдаётся через зависимость FastAPI (Depends) в роутерах.
"""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

settings = get_settings()

# echo=True в debug помогает видеть SQL-запросы в логах при разработке.
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,  # проверяем соединение перед использованием
)

# expire_on_commit=False — объекты остаются доступными после commit.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех ORM-моделей."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Зависимость FastAPI: открывает сессию на время запроса и закрывает её."""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def transaction(db: AsyncSession) -> AsyncIterator[None]:
    """Единица работы (unit of work) на уровне сервиса.

    Репозитории внутри блока вызываются с `commit=False` (только flush),
    commit — один на блок; при любом исключении — rollback, чтобы не остались
    частичные записи (лид без заказа, заказ без брони слота и т.п.).
    """
    try:
        yield
    except BaseException:
        await db.rollback()
        raise
    else:
        await db.commit()
