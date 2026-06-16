.PHONY: help dev stop build setup migrate migration seed test lint format check fix hooks-install clean logs ps

COMPOSE = docker compose
BACKEND = apps/backend
FRONTEND = apps/frontend
TRAINING = training_engine

help:
	@echo "make setup          First-time project setup (includes hook install)"
	@echo "make dev            Start all services (Docker)"
	@echo "make stop           Stop all services"
	@echo "make build          Rebuild all Docker images"
	@echo "make migrate        Run DB migrations"
	@echo "make migration      Create migration (MSG=your message)"
	@echo "make seed           Seed initial data"
	@echo "make test           Run all tests"
	@echo "make lint           Lint all code (report only)"
	@echo "make format         Format all code"
	@echo "make check          Lint + typecheck everything (mirrors CI)"
	@echo "make fix            Auto-fix all lint + format issues"
	@echo "make hooks-install  Install pre-commit git hooks"
	@echo "make logs           Tail container logs"
	@echo "make ps             Show container status"
	@echo "make clean          Remove all containers + volumes"

setup:
	cp -n .env.example .env || true
	cd $(FRONTEND) && npm install
	cd $(BACKEND) && uv venv .venv --python 3.11 && \
	  . .venv/bin/activate && uv pip install -r requirements.txt
	cd $(TRAINING) && uv venv .venv --python 3.11 && \
	  . .venv/bin/activate && uv pip install -r requirements.txt
	$(MAKE) hooks-install
	$(COMPOSE) up -d postgres redis minio minio_init
	sleep 15
	$(COMPOSE) run --rm backend alembic upgrade head
	$(COMPOSE) run --rm backend python -m scripts.seed_data
	@echo "✅ Setup complete. Run 'make dev' to start."

hooks-install:
	uv tool install pre-commit --python 3.11
	uv tool run pre-commit install
	uv tool run pre-commit install --hook-type commit-msg
	@echo "✅ Pre-commit hooks installed."

dev:
	$(COMPOSE) up

dev-gpu:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.gpu.yml up

stop:
	$(COMPOSE) down

build:
	$(COMPOSE) build --no-cache

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) run --rm backend alembic upgrade head

migration:
	$(COMPOSE) run --rm backend alembic revision --autogenerate -m "$(MSG)"

seed:
	$(COMPOSE) run --rm backend python -m scripts.seed_data

db-shell:
	docker exec -it fts_postgres psql -U fts_user -d fts_db

redis-cli:
	docker exec -it fts_redis redis-cli -a $$REDIS_PASSWORD

minio-ui:
	open http://localhost:9001 || xdg-open http://localhost:9001

test:
	cd $(FRONTEND) && npm run test
	cd $(BACKEND) && . .venv/bin/activate && pytest tests/ -v --cov=.
	cd $(TRAINING) && . .venv/bin/activate && pytest tests/ -v

lint:
	cd $(FRONTEND) && npm run lint
	cd $(BACKEND) && . .venv/bin/activate && ruff check .
	cd $(TRAINING) && . .venv/bin/activate && ruff check .

format:
	cd $(FRONTEND) && npx prettier --write .
	cd $(BACKEND) && . .venv/bin/activate && ruff format .
	cd $(TRAINING) && . .venv/bin/activate && ruff format .

check:
	@echo "── ruff lint ──────────────────────────────────────────"
	cd $(BACKEND) && . .venv/bin/activate && ruff check .
	cd $(TRAINING) && . .venv/bin/activate && ruff check .
	@echo "── ruff format ────────────────────────────────────────"
	cd $(BACKEND) && . .venv/bin/activate && ruff format --check .
	cd $(TRAINING) && . .venv/bin/activate && ruff format --check .
	@echo "── ESLint ─────────────────────────────────────────────"
	cd $(FRONTEND) && npm run lint
	@echo "── TypeScript ─────────────────────────────────────────"
	cd $(FRONTEND) && npx tsc --noEmit
	@echo "✅ All checks passed."

fix:
	@echo "── ruff fix ───────────────────────────────────────────"
	cd $(BACKEND) && . .venv/bin/activate && ruff check --fix . && ruff format .
	cd $(TRAINING) && . .venv/bin/activate && ruff check --fix . && ruff format .
	@echo "── prettier fix ───────────────────────────────────────"
	cd $(FRONTEND) && npx prettier --write .
	@echo "── eslint fix ─────────────────────────────────────────"
	cd $(FRONTEND) && npm run lint -- --fix 2>/dev/null || true
	@echo "✅ Auto-fix complete. Run 'make check' to verify."

clean:
	$(COMPOSE) down -v --remove-orphans
	rm -rf $(FRONTEND)/.next $(FRONTEND)/node_modules
	rm -rf $(BACKEND)/.venv $(TRAINING)/.venv
	@echo "✅ Clean complete."
