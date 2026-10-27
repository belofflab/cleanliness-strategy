"""Точка входа FastAPI-приложения.

Фабрика create_app() собирает приложение: обработчики ошибок, middleware,
CORS, роутеры, метаданные. Запуск в проде: uvicorn app.main:app (см. Dockerfile).
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.api.middleware import RequestMetricsMiddleware
from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.errors import install_exception_handlers
from app.core.logging import configure_logging
from app.core.redis import redis_client
from app.core.sentry import init_sentry

settings = get_settings()

# Структурное логирование настраиваем первым, чтобы перехватить логи старта.
configure_logging()

# Инициализируем мониторинг ошибок до создания приложения (no-op без DSN).
init_sentry()


def operation_id(route: APIRoute) -> str:
    """Стабильный operationId для генерации клиентов из OpenAPI: <тег>_<обработчик>.

    Уникальность контролирует tests/test_openapi_contract.py.
    """
    tag = str(route.tags[-1]) if route.tags else "api"
    return f"{tag}_{route.name}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения: освобождаем ресурсы при остановке."""
    yield
    # Корректно закрываем пул соединений Redis при завершении.
    await redis_client.aclose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.2.0",
        debug=settings.debug,
        lifespan=lifespan,
        generate_unique_id_function=operation_id,
    )

    # Единый формат ошибок (detail + error{code,message,request_id,fields}).
    install_exception_handlers(app)

    # Наблюдаемость: тайминг, access-log и метрики на каждый запрос.
    app.add_middleware(RequestMetricsMiddleware)

    # CORS: разрешаем доступ только доверенным доменам фронтенда.
    # Добавлен последним → во внешнем слое стека (обрабатывает preflight).
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Все эндпоинты живут под префиксом /api/v1.
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
