# Makefile платформы PointClean.
# Удобные команды-обёртки над docker compose и инструментами разработки.

# Файл окружения и compose-файлы.
ENV_FILE := deploy/.env
COMPOSE := docker compose --env-file $(ENV_FILE) -f deploy/docker-compose.yml
COMPOSE_DEV := $(COMPOSE) -f deploy/docker-compose.dev.yml
COMPOSE_PROD := docker compose --env-file $(ENV_FILE) -f deploy/docker-compose.prod.yml

.PHONY: help init build up dev down restart logs ps migrate makemigration seed test-api lint-api shell worker-logs beat-logs prod-up prod-build prod-down prod-migrate prod-logs health api-dev-lan mobile-go mobile-tunnel

help: ## Показать список команд
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

init: ## Создать deploy/.env из примера (если ещё нет)
	@test -f $(ENV_FILE) || (cp deploy/.env.example $(ENV_FILE) && echo "Создан $(ENV_FILE) — проверьте значения")

build: ## Собрать образы всех сервисов
	$(COMPOSE) build

up: init ## Запустить весь стек (web + api + worker + beat + postgres + redis)
	$(COMPOSE) up -d

dev: init ## Запустить стек в режиме разработки (api с hot-reload)
	$(COMPOSE_DEV) up

down: ## Остановить и удалить контейнеры
	$(COMPOSE) down

restart: ## Перезапустить сервисы
	$(COMPOSE) restart

logs: ## Хвост логов всех сервисов
	$(COMPOSE) logs -f --tail=100

worker-logs: ## Логи Celery worker
	$(COMPOSE) logs -f --tail=100 worker

beat-logs: ## Логи Celery beat
	$(COMPOSE) logs -f --tail=100 beat

ps: ## Статус контейнеров
	$(COMPOSE) ps

shell: ## Открыть shell внутри контейнера api
	$(COMPOSE) exec api sh

migrate: ## Применить миграции БД (alembic upgrade head)
	$(COMPOSE) exec api alembic upgrade head

makemigration: ## Сгенерировать миграцию: make makemigration m="описание"
	$(COMPOSE) exec api alembic revision --autogenerate -m "$(m)"

seed: ## Заполнить БД начальными данными (авто-применяет миграции перед сидированием)
	$(COMPOSE) exec api alembic upgrade head
	$(COMPOSE) exec api python -m app.seed

test-api: ## Запустить тесты backend (с живой PostgreSQL контейнера)
	$(COMPOSE) exec api pip install -q -r requirements-dev.txt
	$(COMPOSE) exec api pytest

lint-api: ## Проверить backend линтером ruff
	$(COMPOSE) exec api pip install -q -r requirements-dev.txt
	$(COMPOSE) exec api ruff check .

# ===== Тестирование мобильного приложения на телефонах (docs/FREE_TESTING_GUIDE.md) =====
api-dev-lan: ## API без Docker, доступный с телефона в той же Wi-Fi-сети (uvicorn на 0.0.0.0:8000; нужен активный venv)
	cd services/api && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

mobile-go: ## Metro для Expo Go в локальной сети (IP машины подставляется в API-адрес автоматически)
	npm --prefix apps/mobile run go

mobile-tunnel: ## Metro для Expo Go через туннель (телефон в другой сети)
	npm --prefix apps/mobile run go:tunnel

# ===== Production (deploy/docker-compose.prod.yml) =====
prod-build: ## Собрать production-образы
	$(COMPOSE_PROD) build

prod-up: ## Запустить production-стек в фоне
	$(COMPOSE_PROD) up -d --build

prod-down: ## Остановить production-стек
	$(COMPOSE_PROD) down

prod-migrate: ## Применить миграции на production
	$(COMPOSE_PROD) exec api alembic upgrade head

prod-logs: ## Логи production-стека
	$(COMPOSE_PROD) logs -f --tail=100

health: ## Healthcheck всех контейнеров (prod)
	COMPOSE_FILE=deploy/docker-compose.prod.yml ENV_FILE=deploy/.env ./deploy/healthcheck.sh

