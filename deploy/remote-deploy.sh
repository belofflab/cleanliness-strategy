#!/usr/bin/env bash
# Запускается на проде из GitHub Actions (ssh … 'bash -s' < deploy/remote-deploy.sh)
# после успешной сборки и публикации образов в GHCR. Тянет свежие образы и
# перезапускает стек. Идемпотентно и безопасно для повторного запуска.
#
# Требование: на сервере выполнен `docker login ghcr.io` валидным токеном
# с read:packages (иначе pull приватных образов вернёт 403).
set -euo pipefail

REPO_DIR=/opt/clean-comp
COMPOSE="docker compose --env-file deploy/.env -f deploy/docker-compose.prod.yml"

cd "$REPO_DIR"

echo "[deploy] sync working tree to origin/main"
git fetch origin main --quiet
git checkout -f main
git reset --hard origin/main

echo "[deploy] pull GHCR images"
$COMPOSE pull api web

echo "[deploy] apply DB migrations (one-off, additive)"
$COMPOSE run --rm api alembic upgrade head

echo "[deploy] recreate services"
$COMPOSE up -d

echo "[deploy] wait for api health"
for _ in $(seq 1 20); do
  if curl -fsS http://127.0.0.1:8000/api/v1/health >/dev/null 2>&1; then
    echo "[deploy] api healthy"
    break
  fi
  sleep 3
done

echo "[deploy] final health:"
curl -fsS http://127.0.0.1:8000/api/v1/health && echo
echo "[deploy] done"
