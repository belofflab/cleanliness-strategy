#!/usr/bin/env bash
# Быстрая проверка здоровья всего стека PointClean.
# Использование:
#   ./deploy/healthcheck.sh                      # авто-определение compose-файла
#   COMPOSE_FILE=deploy/docker-compose.prod.yml ./deploy/healthcheck.sh
#
# Код возврата: 0 — всё здорово, 1 — есть проблемы (удобно для CI/cron).

set -uo pipefail

# --- Определяем директорию репозитория и compose-файл ---
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_FILE="${ENV_FILE:-$SCRIPT_DIR/.env}"
COMPOSE_FILE="${COMPOSE_FILE:-$SCRIPT_DIR/docker-compose.yml}"

COMPOSE=(docker compose -f "$COMPOSE_FILE")
[ -f "$ENV_FILE" ] && COMPOSE=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
FAIL=0

say()  { printf "%b\n" "$1"; }
ok()   { say "${GREEN}✔${NC} $1"; }
bad()  { say "${RED}x${NC} $1"; FAIL=1; }
warn() { say "${YELLOW}•${NC} $1"; }

say "\n=== PointClean healthcheck ($(date '+%Y-%m-%d %H:%M:%S')) ==="
say "compose: $COMPOSE_FILE\n"

# --- 1. Статус контейнеров ---
say "1) Контейнеры:"
SERVICES=$("${COMPOSE[@]}" ps --services 2>/dev/null)
if [ -z "$SERVICES" ]; then
  bad "Не удалось получить список сервисов (docker compose недоступен или стек не запущен)"
  exit 1
fi

for svc in $SERVICES; do
  cid=$("${COMPOSE[@]}" ps -q "$svc" 2>/dev/null)
  if [ -z "$cid" ]; then
    bad "$svc — контейнер не создан"
    continue
  fi
  state=$(docker inspect -f '{{.State.Status}}' "$cid" 2>/dev/null)
  health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}' "$cid" 2>/dev/null)
  if [ "$state" = "running" ] && { [ "$health" = "healthy" ] || [ "$health" = "n/a" ]; }; then
    ok "$svc — $state${health:+ ($health)}"
  else
    bad "$svc — $state${health:+ ($health)}"
  fi
done

# --- 2. HTTP-проверка API ---
say "\n2) API endpoint /api/v1/health:"
if "${COMPOSE[@]}" exec -T api curl -fsS http://localhost:8000/api/v1/health >/dev/null 2>&1; then
  ok "API отвечает 200 OK"
else
  bad "API не отвечает на /api/v1/health"
fi

# --- 3. PostgreSQL ---
say "\n3) PostgreSQL:"
if "${COMPOSE[@]}" exec -T postgres pg_isready >/dev/null 2>&1; then
  ok "Postgres принимает соединения"
else
  bad "Postgres недоступен"
fi

# --- 4. Redis ---
say "\n4) Redis:"
if "${COMPOSE[@]}" exec -T redis redis-cli ping 2>/dev/null | grep -q PONG; then
  ok "Redis отвечает PONG"
else
  bad "Redis недоступен"
fi

# --- 5. Web (Next.js) ---
say "\n5) Web (Next.js):"
if "${COMPOSE[@]}" exec -T web wget -qO- http://localhost:3000 >/dev/null 2>&1 \
   || "${COMPOSE[@]}" exec -T web curl -fsS http://localhost:3000 >/dev/null 2>&1; then
  ok "Web отвечает"
else
  warn "Web не ответил (возможно, нет curl/wget в образе — проверьте вручную)"
fi

say ""
if [ "$FAIL" -eq 0 ]; then
  ok "Все ключевые сервисы здоровы."
  exit 0
else
  bad "Обнаружены проблемы — смотрите вывод выше и логи: '${COMPOSE[*]} logs'."
  exit 1
fi


