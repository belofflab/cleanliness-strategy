"""Конфигурация сервиса.

Все настройки читаются из переменных окружения (файл .env).
Используем Pydantic Settings — это даёт типизацию и валидацию на старте.
"""

import warnings
from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Дефолт для локальной разработки; в production запрещён (см. валидатор ниже).
DEFAULT_JWT_SECRET = "change-me-in-production"
# Минимальная длина HMAC-ключа для HS256 (RFC 7518, §3.2).
MIN_SECRET_BYTES = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Базовые настройки приложения ---
    app_name: str = "Точка Чистоты API"
    environment: str = Field(default="development")  # development | production
    debug: bool = Field(default=False)

    # --- База данных (async PostgreSQL) ---
    # Пример: postgresql+asyncpg://user:pass@postgres:5432/tochka
    database_url: str = Field(
        default="postgresql+asyncpg://tochka:tochka@postgres:5432/tochka"
    )

    # --- Redis (кэш, rate limiting, брокер сообщений) ---
    redis_url: str = Field(default="redis://redis:6379/0")

    # --- Celery (фоновые задачи) ---
    # По умолчанию используем тот же Redis (broker + result backend).
    celery_broker_url: str = Field(default="")
    celery_result_backend: str = Field(default="")

    # --- CORS: домены фронтенда, которым разрешён доступ к API ---
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )

    # --- Регионы и домены ---
    # Город по умолчанию для заявок, звонков и контента без явного города
    # (бизнес Уфа-first; должен совпадать с DEFAULT_CITY_SLUG в apps/web/lib/city.ts).
    default_city_slug: str = Field(default="ufa")
    # Публичный базовый домен: <slug>.<domain> — городские поддомены,
    # apex-домен — город по умолчанию.
    public_base_domain: str = Field(default="cleanliness.pro")

    # --- Calltracking.ru (динамический коллтрекинг) ---
    # Секрет вебхука: добавляется в URL уведомлений в кабинете CT
    # (?secret=...). Пустой секрет = вебхук отключён (безопасный дефолт).
    calltracking_webhook_secret: str = Field(default="")
    # Соответствие подменных номеров городам: JSON {"+79120000000": "tyumen", ...}.
    # Если номер не найден — город определяется по домену сайта из уведомления.
    calltracking_city_numbers: str = Field(default="")

    # --- Яндекс.Метрика: офлайн-конверсии (обучение автостратегий Директа) ---
    # OAuth-токен с правом management:write для счётчика.
    yandex_metrika_token: str = Field(default="")
    yandex_metrika_counter_id: int = Field(default=109824753)
    # Название цели офлайн-конверсии (создать в Метрике: тип «Офлайн»).
    yandex_metrika_goal_done: str = Field(default="CleaningDone")

    # --- S3 / Yandex Object Storage (медиа: аватары, фото «До/После») ---
    s3_enabled: bool = Field(default=False)
    s3_endpoint_url: str = Field(default="https://storage.yandexcloud.net")
    s3_region: str = Field(default="ru-central1")
    s3_bucket: str = Field(default="")
    s3_access_key_id: str = Field(default="")
    s3_secret_access_key: str = Field(default="")
    # Публичный базовый URL для отдачи объектов (CDN или storage.yandexcloud.net/bucket).
    s3_public_base_url: str = Field(default="")

    # --- SMS-провайдер (OTP-вход) — sms.ru ---
    sms_enabled: bool = Field(default=False)
    sms_ru_api_id: str = Field(default="")

    # --- Telegram (мгновенное уведомление операторов о новом лиде) ---
    # Без токена/чата — mock-режим (ничего не отправляется, сервис не падает).
    telegram_enabled: bool = Field(default=False)
    telegram_bot_token: str = Field(default="")
    telegram_chat_id: str = Field(default="")

    # --- JWT (аутентификация, ролевая модель) ---
    jwt_secret: str = Field(default=DEFAULT_JWT_SECRET)
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_ttl_minutes: int = Field(default=15)
    jwt_refresh_ttl_days: int = Field(default=30)

    # --- Секрет хешей OTP-кодов и refresh-токенов ---
    # Отдельный от JWT_SECRET: компрометация одного ключа не раскрывает второй.
    # Пусто = используется JWT_SECRET (совместимость). Refresh-токены, выданные
    # под старым ключом, продолжают работать до истечения срока (см. identity).
    token_hmac_secret: str = Field(default="")

    # --- Rate limiting (Redis) ---
    # Лимиты — в app/core/rate_limit.py. false — отключить (например, для нагрузочных тестов).
    rate_limit_enabled: bool = Field(default=True)
    # За Nginx реальный IP клиента приходит в X-Real-IP / X-Forwarded-For.
    trust_proxy_headers: bool = Field(default=True)

    # --- Sentry (мониторинг ошибок) ---
    sentry_dsn: str = Field(default="")

    # --- Логирование и метрики (задел под Vector/Promtail/Loki) ---
    # log_json=true → структурные JSON-строки, которые без парсинга
    # подхватывает любой лёгкий сборщик логов.
    log_level: str = Field(default="INFO")
    log_json: bool = Field(default=True)

    @property
    def broker_url(self) -> str:
        """Broker Celery: явный или дефолт на основном Redis."""
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    @model_validator(mode="after")
    def _check_production_secrets(self) -> "Settings":
        """В production дефолтный JWT_SECRET недопустим; слабые ключи — предупреждение.

        Предупреждения (а не ошибка) для длины и TOKEN_HMAC_SECRET — чтобы
        релиз не уронил прод до обновления deploy/.env; см. DEPLOY.md, шаг 2.
        """
        if self.environment != "production":
            return self
        if self.jwt_secret == DEFAULT_JWT_SECRET:
            raise ValueError("JWT_SECRET обязателен в production: openssl rand -hex 32")
        if len(self.jwt_secret.encode("utf-8")) < MIN_SECRET_BYTES:
            warnings.warn(
                f"JWT_SECRET короче {MIN_SECRET_BYTES} байт — сгенерируйте новый: openssl rand -hex 32",
                stacklevel=2,
            )
        if not self.token_hmac_secret:
            warnings.warn(
                "TOKEN_HMAC_SECRET не задан — хеши OTP/refresh считаются на JWT_SECRET; "
                "задайте отдельный ключ: openssl rand -hex 32",
                stacklevel=2,
            )
        return self


@lru_cache
def get_settings() -> Settings:
    """Кэшируем настройки, чтобы не перечитывать .env на каждый запрос."""
    return Settings()
