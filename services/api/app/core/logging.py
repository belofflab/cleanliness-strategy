"""Структурное логирование на loguru.

При `log_json=true` каждая запись — самостоятельная ПЛОСКАЯ JSON-строка в stdout:
`timestamp, level, message, module, logger` + контекст запроса
(`request_id, method, path, status_code, latency_ms`). Плоская структура (без
вложенного `record`) парсится Promtail одним `json`-stage без распаковки.

Стандартный `logging` (uvicorn, fastapi, sqlalchemy, celery) перехватывается в
loguru — чтобы весь вывод сервиса шёл одним форматом через единственный синк.
"""

from __future__ import annotations

import json
import logging
import sys

from loguru import logger

from app.core.config import get_settings

# Имена стандартных логгеров, которые перенаправляем в loguru.
_INTERCEPTED_LOGGERS = (
    "uvicorn",
    "uvicorn.error",
    "uvicorn.access",
    "fastapi",
    "celery",
)

# Человекочитаемый формат для локальной разработки (log_json=false).
_HUMAN_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level> {extra}"
)

_configured = False


def _json_sink(message) -> None:
    """Сериализует запись loguru в ОДНУ плоскую JSON-строку (stdout).

    `extra` (request_id/method/path/status_code/latency_ms и т.п.) разворачивается
    на верхний уровень — удобно для запросов в Loki и парсинга Promtail.
    """
    record = message.record
    payload: dict = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["module"],
        "logger": record["name"],
    }
    # Контекст запроса и любые bind/contextualize-поля — на верхний уровень.
    payload.update(record["extra"])
    if record["exception"] is not None:
        payload["exception"] = "".join(
            __import__("traceback").format_exception(*record["exception"])
        )
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")


class InterceptHandler(logging.Handler):
    """Перенаправляет записи стандартного `logging` в loguru."""

    def emit(self, record: logging.LogRecord) -> None:  # noqa: D102
        # Сопоставляем уровень стандартного logging с уровнем loguru.
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Находим кадр вызова, чтобы loguru показал правильный источник.
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def configure_logging() -> None:
    """Настраивает единый синк loguru и перехват стандартного logging.

    Идемпотентно: повторные вызовы (например, в Celery worker и в web)
    не плодят синки.
    """
    global _configured
    if _configured:
        return

    settings = get_settings()
    level = settings.log_level.upper()

    logger.remove()
    if settings.log_json:
        # Плоская JSON-строка на запись — для Promtail/Loki/Vector.
        logger.add(_json_sink, level=level, backtrace=False, diagnose=False)
    else:
        # Человекочитаемый цветной вывод — для локальной разработки.
        logger.add(
            sys.stdout,
            level=level,
            format=_HUMAN_FORMAT,
            backtrace=False,
            diagnose=False,
        )

    # Корневой logging и шумные библиотечные логгеры — в loguru.
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in _INTERCEPTED_LOGGERS:
        std_logger = logging.getLogger(name)
        std_logger.handlers = [InterceptHandler()]
        std_logger.propagate = False

    _configured = True
