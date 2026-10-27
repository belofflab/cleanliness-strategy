"""Redis-клиент.

Используется для healthcheck и rate limiting (app/core/rate_limit.py);
в перспективе — кэш расчётов и pub/sub real-time событий.
"""

from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()

# Единый клиент на процесс. decode_responses=True — строки вместо bytes.
# Короткие таймауты: недоступный Redis не должен подвешивать запросы
# (лимитер и health работают в режиме fail-open).
redis_client: Redis = Redis.from_url(
    settings.redis_url,
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=1.0,
    socket_timeout=1.0,
)
