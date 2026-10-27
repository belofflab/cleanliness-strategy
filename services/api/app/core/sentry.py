"""Инициализация Sentry для backend (FastAPI + Celery).

Без DSN (SENTRY_DSN пуст) ничего не инициализируется — безопасно для dev.
"""

from app.core.config import get_settings


def _drop_handled_http_exceptions(event, hint):
    """Не шлём в Sentry осознанные HTTP-ответы API (fastapi.HTTPException).

    Это ожидаемые ветки (403 «неверный секрет вебхука», 503 «интеграция не
    настроена» и т.п.) — они замусоривают почту алертами. Реальные
    необработанные ошибки (IntegrityError и прочее) HTTPException не являются
    и доходят до Sentry как раньше.
    """
    exc_info = hint.get("exc_info")
    if exc_info:
        from starlette.exceptions import HTTPException as StarletteHTTPException

        if isinstance(exc_info[1], StarletteHTTPException):
            return None
    return event


def init_sentry() -> None:
    settings = get_settings()
    if not settings.sentry_dsn:
        return

    import sentry_sdk

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        traces_sample_rate=0.1,  # 10% трасс для производительности
        send_default_pii=False,
        before_send=_drop_handled_http_exceptions,
    )
