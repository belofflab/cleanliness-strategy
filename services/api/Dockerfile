# Многоступенчатая сборка не нужна для Python — используем стройный slim-образ.
FROM python:3.12-slim
ARG DEBIAN_MIRROR=https://mirror.yandex.ru/debian
ARG DEBIAN_SECURITY_MIRROR=https://mirror.yandex.ru/debian-security
ARG PIP_INDEX_URL=https://mirror.yandex.ru/pypi/web/simple
ARG PIP_EXTRA_INDEX_URL=https://pypi.org/simple
ARG PIP_TRUSTED_HOST=mirror.yandex.ru

# Не пишем .pyc и не буферизуем stdout (логи видны сразу).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Системные зависимости для asyncpg/сборки минимальны в slim — ставим curl для healthcheck.
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
      sed -i "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}|g; s|https://deb.debian.org/debian|${DEBIAN_MIRROR}|g; s|http://security.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g; s|https://security.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" /etc/apt/sources.list.d/debian.sources; \
    fi \
    && if [ -f /etc/apt/sources.list ]; then \
      sed -i "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}|g; s|https://deb.debian.org/debian|${DEBIAN_MIRROR}|g; s|http://security.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g; s|https://security.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" /etc/apt/sources.list; \
    fi \
    && apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Сначала зависимости — кэш слоёв Docker не инвалидируется при правках кода.
COPY requirements.txt ./
ENV PIP_INDEX_URL=$PIP_INDEX_URL \
    PIP_EXTRA_INDEX_URL=$PIP_EXTRA_INDEX_URL \
    PIP_TRUSTED_HOST=$PIP_TRUSTED_HOST
RUN pip install --no-cache-dir -r requirements.txt

# Затем исходный код приложения и миграции.
COPY . .

EXPOSE 8000

# Запуск production-сервера. Хост 0.0.0.0 обязателен внутри контейнера.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

