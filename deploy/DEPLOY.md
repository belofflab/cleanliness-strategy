# Деплой «Точки Чистоты» на production-сервер

Стек: **web** (Next.js) · **api** (FastAPI) · **worker/beat** (Celery) · **PostgreSQL** · **Redis**.
Целевая директория на сервере: `/opt/clean-comp`. Домены: `cleanliness.pro` (web, город по
умолчанию), `<city>.cleanliness.pro` (городские лендинги), `api.cleanliness.pro` (API).
Наружу контейнеры публикует системный Nginx (эталон конфига — `deploy/nginx/`).

Основной цикл — **автоматический**: push в `main` → CI (проверки → образы в GHCR →
SSH-деплой). Ручные шаги ниже нужны для первичной настройки сервера и аварийных случаев.

---

## 0. Предварительные требования на сервере (Ubuntu)
```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER     # перелогиньтесь после этого
docker compose version            # проверка плагина
```

---

## 1. Клонирование репозитория в /opt/clean-comp
```bash
sudo mkdir -p /opt/clean-comp
sudo chown $USER:$USER /opt/clean-comp
git clone git@github.com:Blanq-Tech/clean-comp.git /opt/clean-comp
cd /opt/clean-comp
```
> На сервере нужен только код compose/конфигов и скриптов деплоя — образы приходят из GHCR.

---

## 2. Настройка окружения
```bash
cp deploy/.env.production.example deploy/.env
nano deploy/.env
```
Обязательно задайте:
- `POSTGRES_PASSWORD` — `openssl rand -hex 24`;
- `JWT_SECRET` — `openssl rand -hex 32` (с дефолтным значением API в production не стартует);
- `TOKEN_HMAC_SECRET` — `openssl rand -hex 32` (отдельный ключ хешей OTP/refresh; без него —
  предупреждение в логе, хеши считаются на `JWT_SECRET`; refresh-токены, выданные до смены
  ключа, продолжают работать до истечения срока);
- `DATABASE_URL` — с тем же паролем, что и `POSTGRES_PASSWORD`;
- `DEFAULT_CITY_SLUG` / `PUBLIC_BASE_DOMAIN` — город по умолчанию и базовый домен;
- при боевых интеграциях — `TELEGRAM_*`, `CALLTRACKING_*`, `YANDEX_METRIKA_*`, `S3_*`, `SMS_*` и `*_ENABLED=true`.

`deploy/.env` в `.gitignore` — никогда не коммитьте секреты.

---

## 3. Доступ к GHCR и первый запуск
```bash
# PAT с правом read:packages (Settings → Developer settings → Tokens).
echo "$GHCR_TOKEN" | docker login ghcr.io -u <github-user> --password-stdin

cd /opt/clean-comp
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env pull api web
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env run --rm api alembic upgrade head
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env ps
```

Сиды справочников (один раз; идемпотентно — можно повторять при изменении сидов):
```bash
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env exec api python -m app.seed
```

---

## 4. Проверка здоровья
```bash
COMPOSE_FILE=deploy/docker-compose.prod.yml ENV_FILE=deploy/.env ./deploy/healthcheck.sh

# Локально на сервере API и web доступны только на 127.0.0.1:
curl -fsS http://127.0.0.1:8000/api/v1/health   # {"status":"ok","database":"ok","timestamp":...}
curl -fsS http://127.0.0.1:3000/api/health      # {"status":"ok","service":"web",...}
```

---

## 5. Nginx
Эталон в репозитории: `deploy/nginx/blanq.tech.conf` (структура upstream-ов `web` → `127.0.0.1:3000`,
`api` → `127.0.0.1:8000`). На сервере боевой конфиг для `cleanliness.pro` /
`*.cleanliness.pro` / `api.cleanliness.pro` живёт в `/etc/nginx/sites-enabled/` —
при изменениях приводите upstream-ы к портам `WEB_HOST_PORT`/`API_HOST_PORT` из `deploy/.env`.

```bash
sudo nginx -t && sudo systemctl reload nginx
# SSL (если сертификата ещё нет):
sudo certbot --nginx -d cleanliness.pro -d www.cleanliness.pro -d ufa.cleanliness.pro \
     -d tyumen.cleanliness.pro -d api.cleanliness.pro
```

---

## 6. CI/CD: проверки → GHCR → авто-деплой

`.github/workflows/build-and-push.yml`:

1. **Проверки** на каждый push/PR: `test-api` (ruff, `alembic upgrade head`, `alembic check`,
   pytest с сервисами PostgreSQL/Redis — интеграционные тесты не пропускаются),
   `check-web` (eslint, tsc, регрессионный скрипт), `check-mobile` (tsc).
2. **Сборка образов** `ghcr.io/blanq-tech/clean-comp-web` и `…-api` (теги `latest` на main,
   имя ветки, `sha-<…>`) — только после зелёных проверок и только на push (не на PR).
3. **Деплой** — только на `main`: по SSH (секреты `SSH_PRIVATE_KEY`, `SSH_HOST`, `SSH_USER`)
   на сервере detached запускается `deploy/remote-deploy.sh`
   (sync main → pull → `alembic upgrade head` одноразовым контейнером → `up -d` → health);
   CI поллит результат из `deploy/last-deploy.log`.

> Для авто-деплоя на сервере должен быть валидный `docker login ghcr.io`
> (токен с `read:packages`). При ротации токена — перелогиньтесь, иначе `pull` упадёт 403.

Ручной релиз (если CI недоступен):
```bash
cd /opt/clean-comp
git pull origin main
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env pull api web
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env run --rm api alembic upgrade head
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env up -d
COMPOSE_FILE=deploy/docker-compose.prod.yml ENV_FILE=deploy/.env ./deploy/healthcheck.sh
```

Откат: указать в `deploy/.env` `API_IMAGE=…:sha-<old>` / `WEB_IMAGE=…:sha-<old>` и выполнить
`pull` + `up -d` (образы иммутабельны и версионированы по sha). Миграции аддитивные —
откат кода без отката схемы безопасен.

---

## 7. Полезные команды
```bash
# Логи
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env logs -f --tail=100
# Бэкап БД
docker compose -f deploy/docker-compose.prod.yml --env-file deploy/.env \
  exec -T postgres pg_dump -U tochka tochka > backup_$(date +%F).sql
```

## 8. SIP-сервер Calltracking и почта

- `deploy/docker-compose.sip.yml` — Asterisk для IP-телефонии Calltracking.ru
  (host network; конфиг с паролем генерируется из `deploy/sip/pjsip.conf.template`, см. комментарии в файле).
- `deploy/docker-compose.mail.yml` + `deploy/mail/SETUP.md` — почтовый стек `mail.blanq.tech`.
- `deploy/scripts/disk-alert.sh` — cron-алерт на заполнение диска (инцидент 2026-09-01:
  лог pc_sip заполнил диск; ротация логов включена во всех compose-файлах).

## 9. Наблюдаемость: логи и аптайм (лёгкий стек)

Отдельный, опциональный стек: **Grafana Loki + Promtail + Grafana + Uptime Kuma**.
Без Elasticsearch/Prometheus — минимальное потребление RAM. Запускается рядом с
основным стеком и читает логи всех контейнеров через Docker-сокет.

```bash
# Поднять стек мониторинга (использует тот же deploy/.env).
docker compose --env-file deploy/.env -f deploy/docker-compose.monitoring.yml up -d

# Проверить валидность конфигурации без запуска.
docker compose -f deploy/docker-compose.monitoring.yml config -q && echo OK
```

| Сервис | Где | Назначение |
|--------|-----|------------|
| Loki | внутренний (`:3100`) | хранилище логов (файловое, ретенция 7 дней) |
| Promtail | — | читает stdout контейнеров (Docker-сокет) → Loki |
| Grafana | `127.0.0.1:3001` | просмотр логов (дашборд «Точка Чистоты — Логи») |
| Uptime Kuma | `127.0.0.1:3002` | пинг `/health` + алерты в Telegram |

Grafana и Uptime Kuma **слушают только localhost** (наружу не выставлены).
Доступ к UI — через SSH-туннель с рабочей машины:

```bash
ssh -L 3001:localhost:3001 -L 3002:localhost:3002 <сервер>
# затем в браузере: http://localhost:3001 (Grafana), http://localhost:3002 (Uptime Kuma)
```

Для постоянного доступа — проксируйте через Nginx с HTTPS и Basic-Auth.

**Grafana.** Логин/пароль — из `GRAFANA_USER`/`GRAFANA_PASSWORD` (по умолчанию `admin`/`admin`,
**обязательно смените** в `deploy/.env`). Источник данных Loki и дашборд провижинятся
автоматически. Полезные запросы LogQL: `{container="pc_api"}`, `{level=~"(?i)error"}`,
`{container="pc_api"} | json | status_code >= 500`.

### Настройка Uptime Kuma (пинг health + алерты в Telegram)

Делается один раз через Web UI (`http://<сервер>:3002`):

1. **Создайте администратора** при первом входе.
2. **Telegram-бот:** в Telegram у `@BotFather` создайте бота → получите `Bot Token`.
   Узнайте `Chat ID` (для группы операторов — добавьте бота в группу и откройте
   `https://api.telegram.org/bot<TOKEN>/getUpdates`, либо используйте `@userinfobot`).
3. **Settings → Notifications → Setup Notification → Telegram:** вставьте `Bot Token`
   и `Chat ID`, нажмите **Test** (должно прийти сообщение), сохраните.
4. **Add New Monitor** для бэкенда:
   - Monitor Type: `HTTP(s)`
   - URL: `http://pc_api:8000/api/v1/health` (если Kuma в одной сети с API; иначе
     публичный `https://api.cleanliness.pro/api/v1/health`)
   - Heartbeat Interval: `60` сек, Retries: `2`, **Accepted Status Codes:** `200`
   - Включите созданное Telegram-уведомление.
5. **Add New Monitor** для фронтенда: URL `http://pc_web:3000/api/health` (или
   публичный `https://cleanliness.pro/api/health`).

Чтобы Uptime Kuma достучался до контейнеров по именам (`pc_api`, `pc_web`),
подключите его к сети основного стека (она называется `deploy_default`):

```bash
docker network connect deploy_default pc_uptime_kuma
```

Иначе мониторьте публичные URL через Nginx — это даже честнее (проверяется весь путь).

При падении `/health` (например, недоступна БД → код `503`) Uptime Kuma за ~1–2 минуты
пришлёт алерт операторам в Telegram.
