# Точка Чистоты — Backend API

FastAPI-сервис платформы клининга. Async-стек: FastAPI + SQLAlchemy 2.0 (asyncpg) +
PostgreSQL + Redis + Celery. Архитектурный аудит и план развития —
[`docs/SYSTEM_AUDIT.md`](../../docs/SYSTEM_AUDIT.md).

## Структура

```
app/
  core/          # config (Pydantic Settings), db (engine + transaction), redis, celery, s3, security,
                 # errors (единый формат ошибок), rate_limit (Redis-лимитер), logging, sentry
  api/           # deps, auth_deps (JWT + RBAC), city_context (город из Host/X-City-Slug), middleware
  api/v1/        # роутеры: health, auth, mobile, admin, pricing, leads, booking, reviews, content, integrations
  modules/       # доменные модули (service + repository): pricing, identity, orders — дальше dispatch,
                 # tracking, checklists, payments, reviews, finance, subscriptions, notifications, realtime
  models/        # ORM-модели (20 таблиц)
  schemas/       # Pydantic DTO
  repositories/  # SQL-доступ (catalog, leads, booking, masters, finance, media, notifications, reviews)
  services/      # бизнес-логика вне модулей: booking, calltracking, telegram, sms, media, yandex_offline,
                 # reviews_sync, city_resolution, phones; pricing/quoting/auth/orders — шимы на modules/*
  tasks/         # Celery: analytics (офлайн-конверсии), reviews (синк), media, runner
  seed.py        # идемпотентные сиды (Тюмень + Уфа)
alembic/         # миграции БД
tests/           # pytest: юнит-тесты и интеграционные (PostgreSQL); openapi_contract.json — снимок API
```

Модульная структура (см. `docs/SYSTEM_AUDIT.md` §7.1): новый код домена — в `app/modules/<домен>/`;
старые пути `app.services.pricing`, `app.services.quoting`, `app.services.auth`, `app.services.orders`,
`app.repositories.users`, `app.repositories.orders` остаются шимами до переноса всех вызовов.

## Ошибки API

Единый формат (поле `detail` сохранено для существующих клиентов):

```json
{"detail": "Слишком много запросов, попробуйте позже",
 "error": {"code": "rate_limited", "message": "…", "request_id": "…", "fields": []}}
```

Доменные ошибки наследуют `app.core.errors.DomainError` (статус + код класса); ошибки
валидации — 422 с человекочитаемым `detail` и списком `error.fields` (без введённых
значений); необработанные исключения — 500 c `request_id` и без внутренних деталей.

## Rate limiting

`app/core/rate_limit.py` (Redis, фиксированное окно; лимиты в `LIMITS`): запрос OTP —
3/телефон/10 мин и 20/IP/час, проверка кода — 10/телефон/10 мин, вход по паролю — 10/IP/15 мин,
`POST /leads` — 20/IP/час, `POST /booking/bookings` — 10/IP/час, вебхук звонков — 120/IP/мин.
Ответ — 429 с `Retry-After`. При недоступном Redis лимитер работает в режиме fail-open
(предупреждение в логе). `RATE_LIMIT_ENABLED=false` отключает лимиты; за прокси IP берётся
из `X-Real-IP`/`X-Forwarded-For` (`TRUST_PROXY_HEADERS`).

## Единицы работы (транзакции)

Многошаговые операции (`services/booking.py::create_booking`, `modules/orders/service.py`)
выполняются в `app.core.db.transaction(db)`: репозитории вызываются с `commit=False`
(только flush), commit один на операцию, при ошибке — rollback. Слот мастера при
бронировании блокируется `SELECT … FOR UPDATE` — параллельная бронь получит
«Выбранный слот недоступен».

## Запуск через Docker (рекомендуется)

Из корня репозитория:

```bash
make init     # создаст deploy/.env из примера
make up       # web + api + worker + beat + postgres + redis
make migrate  # применить миграции
make seed     # заполнить справочники (Тюмень + Уфа)
```

API — `http://localhost:8000`, Swagger — `http://localhost:8000/docs`.

## Локальный запуск без Docker

```bash
cd services/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt        # прод-зависимости + pytest/ruff
uvicorn app.main:app --reload
```

## Проверка здоровья

| Эндпоинт | Назначение |
|----------|------------|
| `GET /api/v1/health` | сервис жив; 503, если недоступна БД (для Uptime Kuma) |
| `GET /api/v1/health/ready` | доступность PostgreSQL и Redis |
| `GET /api/v1/metrics` | in-process счётчики запросов |

## Регионы

Города живут в таблице `cities`; каталог, мастера, слоты и филиалы привязаны к `city_id`.
Город запроса определяется так: `city_slug` в запросе → поддомен `Host`
(`<slug>.<PUBLIC_BASE_DOMAIN>`) → заголовок `X-City-Slug` → `DEFAULT_CITY_SLUG` (по умолчанию `ufa`).
Логика поддоменов — `app/services/city_resolution.py`, общая для API и вебхука звонков.

## Каталог и калькулятор

| Эндпоинт | Назначение |
|----------|------------|
| `GET /api/v1/cities` | активные города |
| `GET /api/v1/cities/{slug}/services` | услуги и доп.услуги города |
| `POST /api/v1/pricing/quote` | динамический расчёт цены и времени |
| `GET /api/v1/content` | city-aware контент и SEO-поля лендинга |

Формула (`app/services/pricing.py`, чистая функция на `Decimal`):

```
base     = base_price + rooms·price_per_room + bathrooms·price_per_bathroom
         + area_sqm·price_per_sqm (тарифы «от м²») + Σ addon.price·qty
base    ×= коэффициент состояния (normal 1.00 | neglected 1.15 | heavy 1.30)
subtotal = base × city.price_multiplier
total    = subtotal − промокод (percent | fixed)
```

```bash
curl -X POST http://localhost:8000/api/v1/pricing/quote \
  -H "Content-Type: application/json" \
  -d '{"city_slug":"ufa","service_type":"general","rooms":2,"bathrooms":1,"addon_codes":["windows"],"promo_code":"CLEAN10"}'
```

## Лиды и собственная CRM

| Эндпоинт | Назначение |
|----------|------------|
| `POST /api/v1/leads` | приём заявки с сайта (квиз, обратный звонок) |
| `POST /api/v1/integrations/calltracking/webhook?secret=…` | звонок Calltracking → лид (идемпотентно) |
| `GET/PATCH /api/v1/admin/leads…` | воронка `new → in_progress → converted / rejected`, ответственный, заметка |
| `POST /api/v1/admin/leads/{id}/convert` | заказ из лида (расчёт единым прайсингом) |

Поток: лид **всегда сохраняется в БД** (статус `new`), операторов мгновенно пингует
Telegram (фоном, `TELEGRAM_*`; без ключей — mock). Телефон нормализуется до
`+7XXXXXXXXXX` — единый формат с учётками пользователей, по нему клиент видит свои
заказы в мобильном приложении, работает дедуп звонков и уведомления о статусе.

## Букинг

| Эндпоинт | Назначение |
|----------|------------|
| `GET /api/v1/booking/masters?city_slug=ufa` | мастера города (по рейтингу) |
| `GET /api/v1/booking/availability?city_slug=ufa&date=YYYY-MM-DD&master_id=…` | свободные слоты |
| `POST /api/v1/booking/bookings` | расчёт → лид → заказ → бронь слота |

## Заказы и статусы

Жизненный цикл: `new → assigned → in_progress → done`, `cancelled` из любого
нетерминального статуса (`app/models/orders.py::ORDER_TRANSITIONS`). Клинер из
мобайла переводит **свой** заказ только в `in_progress`/`done`; менеджер — любой
допустимый переход. Статус `done` отправляет офлайн-конверсию в Яндекс.Метрику
(Celery, `YANDEX_METRIKA_*`; без токена — mock).

## Аутентификация и роли

Роли: `client | master | manager | admin` — единая таблица `users`.
Клиент/мастер входят по телефону через OTP (sms.ru, без ключа — mock: код в `debug_code`
вне production); менеджер/админ — по паролю (bcrypt). Токены: JWT access (15 мин) +
refresh (30 дней) с ротацией и отзывом; refresh-токены живут семьями по устройству —
повторное предъявление отозванного токена отзывает всю семью (защита от кражи), logout
отзывает семью целиком. Роль `master` выдаётся только по карточке мастера, заведённой
менеджером с этим телефоном (самозапись клинером невозможна; клиент с такой карточкой
становится клинером при входе с `role=master`). Защита эндпоинтов — `require_roles(...)`
из `app/api/auth_deps.py`. Хеши OTP/refresh считаются на `TOKEN_HMAC_SECRET`
(отдельно от `JWT_SECRET`; при смене ключа старые refresh-токены принимаются до истечения).

| Эндпоинт | Назначение |
|----------|------------|
| `POST /api/v1/auth/otp/request`, `/auth/otp/verify` | вход client/master |
| `POST /api/v1/auth/login` | вход staff (телефон/email + пароль) |
| `POST /api/v1/auth/refresh`, `/auth/logout` | ротация/отзыв refresh |
| `GET /api/v1/auth/me` | профиль по access-токену |

## Мобильное и админское API

- `/api/v1/mobile/*` (bearer): заказы клинера/клиента, смена статуса, профиль, уведомления, push-токены.
- `/api/v1/admin/*` (manager/admin): заказы (канбан, назначение), лиды, пользователи (RBAC),
  клинеры, финансы, медиа (S3 presign/upload), кейсы «До/После», отзывы.

## Миграции и сиды

```bash
make migrate   # alembic upgrade head
make seed      # python -m app.seed — идемпотентно (tyumen + ufa)
alembic check  # ORM-модели и миграции не расходятся (гоняется в CI)
```

Миграции только аддитивные; правки применённых ревизий запрещены.

## Тесты

```bash
cd services/api && pip install -r requirements-dev.txt
ruff check .
pytest                       # юнит-тесты; интеграционные пропускаются без БД
DATABASE_URL=postgresql+asyncpg://tochka:tochka@localhost:5432/tochka pytest   # с живой PostgreSQL
```

Интеграционные тесты (маркер `integration`: контент, сиды, букинг, OTP-поток) нужны
живой PostgreSQL и в CI выполняются против сервиса `postgres`. Локально без БД
они помечаются `skipped`, юнит-тесты (цены, машина статусов, RBAC, парсер вебхука,
криптопримитивы) работают всегда.

## Переменные окружения

См. `deploy/.env.example`. Ключевые: `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`,
`DEFAULT_CITY_SLUG`, `PUBLIC_BASE_DOMAIN`, `JWT_SECRET`, `SMS_*`, `TELEGRAM_*`,
`CALLTRACKING_*`, `YANDEX_METRIKA_*`, `S3_*`, `SENTRY_DSN`, `LOG_LEVEL`/`LOG_JSON`.
Интеграции без ключей работают в mock-режиме — сервис не падает.
