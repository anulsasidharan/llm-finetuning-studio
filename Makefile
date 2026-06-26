.PHONY: help dev stop build setup migrate migration seed sync-gpu-pricing test lint format check fix hooks-install clean logs ps \
        prod prod-gpu prod-build prod-stop prod-migrate prod-logs prod-ps prod-clean

COMPOSE      = docker compose
COMPOSE_PROD = docker compose -f docker-compose.prod.yml
BACKEND      = apps/backend
FRONTEND     = apps/frontend
TRAINING     = training_engine

help:
	@echo "── Development ─────────────────────────────────────────"
	@echo "make setup          First-time project setup (includes hook install)"
	@echo "make dev            Start all services (Docker)"
	@echo "make stop           Stop all services"
	@echo "make build          Rebuild all Docker images"
	@echo "make migrate        Run DB migrations"
	@echo "make migration      Create migration (MSG=your message)"
	@echo "make seed           Seed initial data"
	@echo "make sync-gpu-pricing  Refresh GPU pricing from RunPod + Lambda Labs APIs"
	@echo "make test           Run all tests"
	@echo "make lint           Lint all code (report only)"
	@echo "make format         Format all code"
	@echo "make check          Lint + typecheck everything (mirrors CI)"
	@echo "make fix            Auto-fix all lint + format issues"
	@echo "make hooks-install  Install pre-commit git hooks"
	@echo "make logs           Tail container logs"
	@echo "make ps             Show container status"
	@echo "make clean          Remove all containers + volumes"
	@echo "── Production ──────────────────────────────────────────"
	@echo "make prod-build     Build production images (requires .env.prod)"
	@echo "make prod           Start production stack (detached)"
	@echo "make prod-gpu       Start production stack + GPU training engine"
	@echo "make prod-stop      Stop production stack"
	@echo "make prod-migrate   Run DB migrations against prod database"
	@echo "make prod-logs      Tail production logs"
	@echo "make prod-ps        Show production container status"
	@echo "make prod-clean     Remove prod containers + volumes (DESTRUCTIVE)"

setup:
	cp -n .env.example .env || true
	cd $(FRONTEND) && npm install
	cd $(BACKEND) && uv venv .venv --python 3.11 && \
	  uv pip install --python .venv -r requirements.txt
	cd $(TRAINING) && uv venv .venv --python 3.11 && \
	  uv pip install --python .venv torch==2.3.0 torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu && \
	  uv pip install --python .venv -r requirements.txt
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

sync-gpu-pricing:
	$(COMPOSE) run --rm backend python -m scripts.sync_gpu_pricing

db-shell:
	docker exec -it fts_postgres psql -U fts_user -d fts_db

redis-cli:
	docker exec -it fts_redis redis-cli -a $$REDIS_PASSWORD

minio-ui:
	open http://localhost:9001 || xdg-open http://localhost:9001

test:
	cd $(FRONTEND) && npm run test
	cd $(BACKEND) && uv run --python .venv pytest tests/ -v --cov=.
	cd $(TRAINING) && uv run --python .venv pytest tests/ -v

lint:
	cd $(FRONTEND) && npm run lint
	cd $(BACKEND) && uv run --python .venv ruff check .
	cd $(TRAINING) && uv run --python .venv ruff check .

format:
	cd $(FRONTEND) && npx prettier --write .
	cd $(BACKEND) && uv run --python .venv ruff format .
	cd $(TRAINING) && uv run --python .venv ruff format .

check:
	@echo "── ruff lint ──────────────────────────────────────────"
	cd $(BACKEND) && uv run --python .venv ruff check .
	cd $(TRAINING) && uv run --python .venv ruff check .
	@echo "── ruff format ────────────────────────────────────────"
	cd $(BACKEND) && uv run --python .venv ruff format --check .
	cd $(TRAINING) && uv run --python .venv ruff format --check .
	@echo "── ESLint ─────────────────────────────────────────────"
	cd $(FRONTEND) && npm run lint
	@echo "── TypeScript ─────────────────────────────────────────"
	cd $(FRONTEND) && npx tsc --noEmit
	@echo "✅ All checks passed."

fix:
	@echo "── ruff fix ───────────────────────────────────────────"
	cd $(BACKEND) && uv run --python .venv ruff check --fix . && uv run --python .venv ruff format .
	cd $(TRAINING) && uv run --python .venv ruff check --fix . && uv run --python .venv ruff format .
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

# ── Production targets ──────────────────────────────────────────────────────

prod-build:
	@test -f .env.prod || (echo "❌ .env.prod not found — copy .env.prod.example and fill in values" && exit 1)
	$(COMPOSE_PROD) build --no-cache

prod:
	@test -f .env.prod || (echo "❌ .env.prod not found — copy .env.prod.example and fill in values" && exit 1)
	$(COMPOSE_PROD) up -d

prod-gpu:
	@test -f .env.prod || (echo "❌ .env.prod not found — copy .env.prod.example and fill in values" && exit 1)
	$(COMPOSE_PROD) --profile gpu up -d

prod-stop:
	$(COMPOSE_PROD) down

prod-migrate:
	$(COMPOSE_PROD) run --rm backend alembic upgrade head

prod-logs:
	$(COMPOSE_PROD) logs -f

prod-ps:
	$(COMPOSE_PROD) ps

prod-clean:
	@echo "⚠️  This will destroy all production volumes. Press Ctrl+C to cancel."
	@sleep 5
	$(COMPOSE_PROD) down -v --remove-orphans
	@echo "✅ Production clean complete."
