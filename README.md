# Точка Чистоты — платформа клинингового сервиса

Продакшен-платформа сетевого клининга: лендинг с квизом и SEO-посадочными,
собственная CRM (лиды, заказы, клинеры, финансы), мобильное приложение и единый
backend API. Города: **Уфа** (по умолчанию) и **Тюмень** (SEO-прогрев, заявки
принимаются). Технический аудит и план развития — [`docs/SYSTEM_AUDIT.md`](docs/SYSTEM_AUDIT.md).

| Слой | Технологии |
|------|------------|
| Web | Next.js 16 (App Router, `proxy.ts`), React 19, Tailwind CSS 4, framer-motion |
| Mobile | Expo SDK 51, expo-router, TypeScript strict, expo-secure-store |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2, Alembic, Celery |
| Данные | PostgreSQL 16, Redis 7 |
| Интеграции | Telegram (пинг операторам о лиде), sms.ru (OTP), Calltracking.ru (звонки + подмена номеров), Яндекс.Метрика (цели, офлайн-конверсии), Yandex Object Storage (S3), Sentry |
| Инфраструктура | Docker Compose, GitHub Actions → GHCR → авто-деплой по SSH, Nginx, Loki/Promtail/Grafana/Uptime Kuma |

---

## Архитектура репозитория

```
clean-comp/ (монорепо)
├── apps/
│   ├── web/                  # Next.js: лендинг, /[city], /[city]/[service], /admin (CRM), /spasibo
│   │   ├── app/ components/ lib/ public/
│   │   ├── proxy.ts          # host/cookie → /[city] (Next 16, замена middleware)
│   │   └── Dockerfile        # output: standalone, контекст сборки = корень репо
│   └── mobile/               # Expo: OTP-вход, расчёт, слоты, бронирование (клиент)
├── services/
│   └── api/                  # FastAPI — см. services/api/README.md
│       ├── app/
│       │   ├── core/         # config, async-БД, redis, celery, s3, security, logging, sentry
│       │   ├── api/          # v1-роутеры, RBAC (auth_deps), city_context, middleware
│       │   ├── models/       # ORM (20 таблиц)
│       │   ├── schemas/      # Pydantic DTO
│       │   ├── repositories/ # SQL
│       │   ├── services/     # бизнес-логика: pricing, quoting, orders, booking, auth, calltracking…
│       │   ├── tasks/        # Celery: офлайн-конверсии, синк отзывов
│       │   └── seed.py       # идемпотентные сиды (Тюмень + Уфа)
│       ├── alembic/          # миграции 0001…
│       └── tests/            # pytest: юнит + интеграционные (PostgreSQL)
├── deploy/                   # compose (dev/prod/monitoring/sip/mail), nginx, remote-deploy.sh
├── docs/                     # SYSTEM_AUDIT.md
├── .github/workflows/        # CI: проверки → сборка образов → GHCR → деплой (main)
├── package.json              # npm workspaces (apps/web); mobile ставится отдельно
└── Makefile                  # обёртки над docker compose
```

---

## Вариант A. Полный стек локально (Docker)

Запускает frontend, backend, Celery, PostgreSQL и Redis одной командой.

```bash
make init      # создаст deploy/.env из примера
make build     # соберёт образы
make up        # поднимет весь стек
make migrate   # применит миграции БД
make seed      # заполнит данными (Тюмень + Уфа: услуги, допы, мастера, слоты, промокод, кейсы)
```

После запуска:

| Сервис | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend (Swagger) | http://localhost:8000/docs |
| Health | http://localhost:8000/api/v1/health |

Полезные команды:

```bash
make logs      # логи всех сервисов
make ps        # статус контейнеров
make dev       # backend с hot-reload (uvicorn --reload)
make down      # остановить и удалить контейнеры
make test-api  # тесты backend внутри контейнера (с живой PostgreSQL)
```

---

## Вариант B. Раздельный запуск (без Docker)

Frontend (монорепо, npm workspaces):

```bash
npm install          # из корня — поставит зависимости apps/web
npm run dev:web      # http://localhost:3000
```

Backend:

```bash
cd services/api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # http://localhost:8000
```

Celery worker и beat (фоновые задачи) — отдельными процессами:

```bash
cd services/api && source .venv/bin/activate
celery -A app.core.celery_app.celery_app worker --loglevel=info
celery -A app.core.celery_app.celery_app beat --loglevel=info
```

Mobile:

```bash
cd apps/mobile && npm install && cp .env.example .env && npx expo start
```

Фронтенд устойчив к отсутствию бэкенда: формы покажут успех, кейсы и отзывы
возьмутся из локального фоллбэка. С бэкендом — реальные лиды в CRM и данные городов.

---

## API (v1)

Базовый префикс: `/api/v1`. Полная интерактивная документация — `/docs`.

| Группа | Эндпоинты |
|--------|-----------|
| Здоровье | `GET /health`, `GET /health/ready`, `GET /metrics` |
| Каталог и расчёт | `GET /cities`, `GET /cities/{slug}/services`, `POST /pricing/quote`, `GET /content` (город по Host / `X-City-Slug`) |
| Лиды и букинг | `POST /leads`, `GET /booking/masters`, `GET /booking/availability`, `POST /booking/bookings` |
| Контент сайта | `GET /reviews`, `GET /before-after` |
| Аутентификация | `POST /auth/otp/request`, `POST /auth/otp/verify` (client/master по SMS-коду), `POST /auth/login` (manager/admin по паролю), `POST /auth/refresh`, `POST /auth/logout`, `GET /auth/me` |
| Мобильное API (bearer) | `GET /mobile/orders?scope=active\|completed`, `GET /mobile/orders/{id}`, `PATCH /mobile/orders/{id}/status` (клинер: `in_progress`/`done`), `GET /mobile/profile`, `GET /mobile/notifications`, `POST /mobile/notifications/{id}/read`, `POST /mobile/push-tokens` |
| Админ-CRM (manager/admin) | `/admin/orders`, `/admin/orders/board`, `/admin/orders/{id}/status`, `/admin/orders/{id}/assign`, `/admin/leads`, `/admin/leads/summary`, `/admin/leads/{id}`, `/admin/leads/{id}/convert`, `/admin/users`, `/admin/masters`, `/admin/finance`, `/admin/finance/summary`, `/admin/media/upload`, `/admin/media/presign`, `/admin/before-after`, `/admin/reviews`, `/admin/reviews/sync` |
| Интеграции | `POST /integrations/calltracking/webhook?secret=…` (звонок → лид) |

Город без явного `city_slug` (лид, букинг, звонок, `/content` на apex-домене) —
`DEFAULT_CITY_SLUG` (по умолчанию `ufa`); городские поддомены — `<slug>.<PUBLIC_BASE_DOMAIN>`.
Телефоны лидов хранятся в едином формате `+7XXXXXXXXXX` — по ним клиент видит
свои заказы в мобильном приложении.

Пример расчёта:

```bash
curl -X POST http://localhost:8000/api/v1/pricing/quote \
  -H "Content-Type: application/json" \
  -d '{"city_slug":"ufa","service_type":"general","rooms":2,"bathrooms":1,"addon_codes":["windows"],"promo_code":"CLEAN10"}'
```

Подробнее по backend (миграции, сиды, потоки, тесты): `services/api/README.md`.

---

## Переменные окружения

Frontend (`apps/web/.env`, см. `apps/web/.env.example`; в проде инлайнятся при сборке образа в CI):

```bash
NEXT_PUBLIC_SITE_URL=https://cleanliness.pro                 # канонический URL для SEO
NEXT_PUBLIC_API_URL=https://api.cleanliness.pro/api/v1       # адрес backend API
NEXT_PUBLIC_CALLTRACKING_SCRIPT_URL=                          # скрипт подмены номеров (пусто = выкл.)
```

Backend и инфраструктура (`deploy/.env`, см. `deploy/.env.example` и `deploy/.env.production.example`):

```bash
DATABASE_URL=postgresql+asyncpg://tochka:tochka@postgres:5432/tochka
REDIS_URL=redis://redis:6379/0
CORS_ORIGINS=["http://localhost:3000"]
DEFAULT_CITY_SLUG=ufa                 # город по умолчанию
PUBLIC_BASE_DOMAIN=cleanliness.pro    # базовый домен городских поддоменов
JWT_SECRET=change-me-in-production    # в проде обязателен (openssl rand -hex 32)
TOKEN_HMAC_SECRET=                    # отдельный ключ хешей OTP/refresh (пусто = JWT_SECRET)
RATE_LIMIT_ENABLED=true               # лимиты OTP/login/leads/booking/webhook (Redis, fail-open)
TRUST_PROXY_HEADERS=true              # IP клиента из X-Real-IP / X-Forwarded-For за Nginx
SMS_ENABLED=false                     # true + SMS_RU_API_ID для реальных OTP
TELEGRAM_ENABLED=false                # true + TELEGRAM_BOT_TOKEN/CHAT_ID — пинг операторам о лиде
CALLTRACKING_WEBHOOK_SECRET=          # секрет вебхука звонков (пусто = вебхук выключен)
YANDEX_METRIKA_TOKEN=                 # офлайн-конверсии «Клининг выполнен» (пусто = mock)
S3_ENABLED=false                      # true + ключи Yandex Object Storage для медиа
SENTRY_DSN=
LOG_LEVEL=INFO                        # структурные JSON-логи (LOG_JSON=true) под Promtail
```

Mobile (`apps/mobile/.env`, см. `.env.example`): `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_DEFAULT_CITY`.

---

## SEO

- City-aware `generateMetadata` (`app/[city]/layout.tsx`, `lib/seo.ts`): canonical, hreflang между городами, OpenGraph.
- JSON-LD `HomeAndConstructionBusiness` + `FAQPage` (`components/CityJsonLd.tsx`), `Service` на посадочных услуг.
- `robots.ts`, `sitemap.ts` (главные города + посадочные услуг), `manifest.ts`.

---

## Проверки качества

```bash
# backend (интеграционные тесты требуют DATABASE_URL на живую PostgreSQL; без неё они пропускаются)
cd services/api && pip install -r requirements-dev.txt
ruff check . && alembic upgrade head && alembic check && pytest

# web
npm run lint:web
(cd apps/web && npx tsc --noEmit)
node apps/web/scripts/city-ui-regression-check.mjs

# mobile
(cd apps/mobile && npm ci && npx tsc --noEmit)
```

CI (`.github/workflows/build-and-push.yml`) прогоняет те же проверки на каждый push
и pull request (backend — с сервисами PostgreSQL/Redis). Образы собираются и
деплоятся только после зелёных проверок.

---

## Деплой

Push в `main` → GitHub Actions: проверки → сборка образов `api`/`web` → публикация в
GHCR → по SSH на сервер `/opt/clean-comp` выполняется `deploy/remote-deploy.sh`
(sync main → pull образов → `alembic upgrade head` → `up -d` → health). Прод образы
**не собирает**, только тянет. Домены: `cleanliness.pro` (web, город по умолчанию),
`<city>.cleanliness.pro` (городские лендинги), `api.cleanliness.pro` (API).
Сиды (`make prod-migrate` + `python -m app.seed`) применяются вручную.

Подробно — `deploy/DEPLOY.md`.

---

## Наблюдаемость (логи + аптайм)

Лёгкий стек без Elasticsearch/Prometheus: **Loki + Promtail + Grafana + Uptime Kuma**.

- Бэкенд (FastAPI) и фронтенд (Next.js) пишут структурные **JSON-логи в stdout** одной
  строкой (`timestamp/level/message/module` + `request_id/method/path/status_code/latency_ms`).
- Каждый запрос получает `X-Request-ID` и `X-Response-Time-ms`; базовые метрики — `GET /api/v1/metrics`.
- Health-эндпоинты для аптайм-мониторинга: `GET /api/v1/health` (с проверкой БД) и `GET /api/health` (Next.js).
- Promtail собирает логи всех контейнеров через Docker-сокет → Loki; Grafana показывает
  готовый дашборд; Uptime Kuma пингует `/health` и шлёт алерты операторам в Telegram.
- Cron-алерт на заполнение диска: `deploy/scripts/disk-alert.sh`.

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.monitoring.yml up -d
# Grafana → http://localhost:3001 · Uptime Kuma → http://localhost:3002
```

Подробная настройка (включая Telegram-алерты) — `deploy/DEPLOY.md`, раздел 9.

---

## Дорожная карта

Целевая архитектура (потоки Клиент/Клинер в мобильном приложении, real-time статусы и
трекинг, оплаты, чек-листы и фото, подписки), изменения схемы БД и пошаговый план —
в [`docs/SYSTEM_AUDIT.md`](docs/SYSTEM_AUDIT.md).
