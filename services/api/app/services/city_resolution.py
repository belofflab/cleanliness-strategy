"""Определение города по доменному имени — общая логика API и интеграций.

Единый источник правды о «городских» поддоменах: `ufa.<base_domain>` → `ufa`.
Базовый домен и город по умолчанию задаются настройками
(`PUBLIC_BASE_DOMAIN`, `DEFAULT_CITY_SLUG`), а не зашиты в код.
"""

from __future__ import annotations

# Служебные поддомены, которые никогда не являются городом.
RESERVED_SUBDOMAINS = frozenset({"www", "api", "mail", "admin", "blanq"})


def extract_city_slug_from_host(host: str | None, base_domain: str) -> str | None:
    """Возвращает slug города из поддомена либо None.

    `ufa.cleanliness.pro` → `ufa`; apex/`www`/служебные поддомены → None.
    Для локальной разработки поддерживается `<slug>.localhost`.
    Ближайшая к базовому домену метка считается городом (как и в web `lib/city.ts`).
    """
    if not host:
        return None

    hostname = host.split(":", 1)[0].strip().lower().rstrip(".")
    if not hostname:
        return None

    for suffix in (f".{base_domain.strip().lower()}", ".localhost"):
        if not hostname.endswith(suffix):
            continue
        prefix = hostname[: -len(suffix)]
        if not prefix:
            return None
        slug = prefix.split(".")[-1]
        if slug in RESERVED_SUBDOMAINS:
            return None
        return slug

    return None
