"""Запуск async-корутин внутри Celery-воркера.

Каждая задача получает СВЕЖИЙ SQLAlchemy-движок, созданный в процессе воркера
(пул соединений нельзя разделять между форками), и корректно освобождает его.
"""

from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, Callable, TypeVar

_T = TypeVar("_T")


def _run_in_task(
    coro_factory: Callable[[], Coroutine[Any, Any, _T]],
    *,
    dispose_engine: bool = True,
) -> _T:
    """Выполняет корутину в новом event loop процесса Celery-воркера."""

    async def _wrapper() -> _T:
        try:
            return await coro_factory()
        finally:
            if dispose_engine:
                from app.core.db import engine

                await engine.dispose()

    return asyncio.run(_wrapper())


def _run_async(coro: Coroutine[Any, Any, _T]) -> _T:
    """Совместимость: выполнить готовую корутину."""
    return _run_in_task(lambda: coro)
