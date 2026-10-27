"""Окружение Alembic для async-движка (SQLAlchemy 2.0 + asyncpg).

URL базы и metadata берём из приложения, чтобы не дублировать конфигурацию.
В Блоке 1 сюда подключатся реальные модели через app.core.db.Base.
"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from sqlalchemy import pool

from app.core.config import get_settings
from app.core.db import Base

# Подтягиваем модели, чтобы их таблицы попали в Base.metadata (autogenerate).
import app.models  # noqa: F401,E402

config = context.config

# Подставляем URL из настроек приложения.
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Запуск миграций в online-режиме на async-движке."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_offline() -> None:
    """Offline-режим: генерация SQL без подключения к БД."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

