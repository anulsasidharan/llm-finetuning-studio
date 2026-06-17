# MEMORY.md — LLM Fine-Tuning Studio
# Claude Code reads this at the start of every session to restore context instantly.
# Update this file after every significant session.

## PROJECT IDENTITY
- Name: LLM Fine-Tuning Studio
- Owner: Anu Sasidharan | OrionVexa (orionvexa.ca)
- GitHub: https://github.com/anulsasidharan/llm-finetuning-studio
- Type: Standalone independent app — shares NOTHING with Unified RAG Studio
- Stack: Next.js 14 + FastAPI + PostgreSQL + Redis + MinIO + Celery

## CURRENT PHASE
- Phase: 1 — Infrastructure & Skeleton
- Active Week: 2
- Last completed task: PHASE1-WEEK2-001 — core/config.py full implementation (2026-06-17)
- Next task: PHASE1-WEEK2-002 — core/database.py async SQLAlchemy engine + session factory

## GIT WORKFLOW
- main branch:     production-ready only — never commit directly
- develop branch:  integration branch — never commit directly
- feature branches: cut from develop, named feat/TASK-ID-description
- all PRs target:  develop (never main)
- develop → main:  only at end of each phase milestone
- PR template:     .github/PULL_REQUEST_TEMPLATE.md
- CI runs on:      push to develop + all PRs

## ARCHITECTURE DECISIONS (DO NOT REVISIT)
- Frontend: Next.js 14 App Router only — never Pages Router
- State: TanStack Query (server) + Zustand (client) + React Hook Form + Zod (forms)
- Python package manager: uv — never bare pip
- DB ORM: SQLAlchemy 2 async — never sync sessions
- Storage: MinIO in dev, S3 in production — client in core/storage.py
- Task queue: Celery with Redis broker — 3 queues: training, export, default
- Logging: structlog JSON — never print()
- Config: pydantic-settings Settings class — never os.environ directly
- Auth: JWT (python-jose) + bcrypt (passlib) — self-contained, no external auth

## PORT MAP (memorize — never change)
- Frontend:      localhost:3000  (container: fts_frontend)
- Backend API:   localhost:8000  (container: fts_backend)
- PostgreSQL:    localhost:5433  (container: fts_postgres)   ← 5433 not 5432
- Redis:         localhost:6380  (container: fts_redis)      ← 6380 not 6379
- MinIO API:     localhost:9000  (container: fts_minio)
- MinIO Console: localhost:9001  (container: fts_minio)
- Flower:        localhost:5555  (container: fts_flower)

## DOCKER FACTS
- Compose project name: llm-finetuning-studio
- Network: fts_network (bridge, isolated)
- All volumes prefixed: fts_postgres_data, fts_redis_data, fts_minio_data, fts_hf_cache
- All containers prefixed: fts_*
- GPU training: docker compose -f docker-compose.yml -f docker-compose.gpu.yml up

## DIRECTORY SHORTCUTS
- Frontend root:    apps/frontend/
- Backend root:     apps/backend/
- ML engine root:   training_engine/
- API routes:       apps/backend/api/v1/routes/
- DB models:        apps/backend/models/
- Pydantic schemas: apps/backend/schemas/
- Business logic:   apps/backend/services/
- Celery tasks:     apps/backend/tasks/
- DB migrations:    apps/backend/migrations/versions/
- React components: apps/frontend/components/
- Next.js pages:    apps/frontend/app/(dashboard)/
- Custom hooks:     apps/frontend/hooks/
- Shared types:     apps/frontend/types/index.ts

## ENVIRONMENT
- .env is at repo root — never commit it
- DATABASE_URL uses host alias "postgres" inside Docker, "localhost:5433" outside
- REDIS_URL uses host alias "redis" inside Docker, "localhost:6380" outside
- HF_CACHE_DIR=/app/.cache/huggingface (shared volume fts_hf_cache)

## FINE-TUNING METHODS SUPPORTED
SFT → trl.SFTTrainer
LoRA → peft.LoraConfig + SFTTrainer
QLoRA → LoRA + BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4")
DPO → trl.DPOTrainer (needs chosen/rejected pairs, doubles VRAM for reference model)
ORPO → trl.ORPOTrainer (single-pass, no reference model, lower VRAM than DPO)
RLHF → trl.PPOTrainer + RewardTrainer (Phase 4 stretch goal)

## BASE MODELS IN CATALOG
meta-llama/Meta-Llama-3-8B, meta-llama/Meta-Llama-3-8B-Instruct
meta-llama/Meta-Llama-3-70B
mistralai/Mistral-7B-v0.3, mistralai/Mistral-7B-Instruct-v0.3
microsoft/Phi-3-mini-4k-instruct, microsoft/Phi-3-medium-4k-instruct
Qwen/Qwen2-7B, Qwen/Qwen2-72B
google/gemma-2-9b, google/gemma-2-27b
codellama/CodeLlama-7b-hf, codellama/CodeLlama-34b-hf

## DATASET FORMATS
alpaca:   {"instruction": "...", "input": "...", "output": "..."}
sharegpt: {"conversations": [{"from": "human", "value": "..."}, {"from": "gpt", "value": "..."}]}
chatml:   {"messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}

## WEBSOCKET PATTERN
Channel: /ws/training/{job_id}
Redis pub/sub channel: training_metrics:{job_id}
Callback: training_engine/utils/callbacks.py → MetricsCallback extends TrainerCallback
Payload type fields: metrics_update | status_change

## SESSION LOG (append after each session)
| Date | What was done | Files changed | Next task |
|------|--------------|---------------|-----------|
| 2026-06-15 | PHASE1-WEEK1-001: Full project infrastructure setup — 62 dirs, all Docker services, Next.js 14 + shadcn, FastAPI + uv, training_engine bootstrap, health endpoint confirmed | docker-compose.yml, all Dockerfiles, .env.example, .gitignore, Makefile, apps/backend/main.py, core/config.py, alembic.ini, start.sh, 79 files committed | PHASE1-WEEK1-002: Makefile verification + README.md |
| 2026-06-17 | PHASE1-WEEK1-002: Verified Makefile targets (help/ps/logs/lint) by running underlying commands directly — `make` binary not installed in this Windows/Git Bash env, so verification was done via `docker compose ps/logs` and `uv run ruff check` on backend + training_engine (both clean); no Makefile fixes needed. Wrote full README.md (badges, features, tech stack, quickstart, service URLs, fine-tuning methods, project structure, dev commands, contributing, license placeholder) | README.md | PHASE1-WEEK2-001: core/config.py full implementation |
| 2026-06-17 | PHASE1-WEEK2-001: Extended `Settings` to cover every var in `.env.example` (App/Postgres/Redis/MinIO/AWS S3/HuggingFace/Cloud GPU Vendors/GPU Pricing/Notifications/Training Engine), added `get_settings()` w/ `lru_cache`. Found+fixed a latent bug: `env_file=".env"` was cwd-relative and broke when running `uv run` from `apps/backend` (no local `.env` there); switched to an absolute path resolved from `config.py`'s own location (`Path(__file__).resolve().parents[3] / ".env"`). Verified settings import cleanly, `ruff check` clean, confirmed via `git stash` that remaining `ruff format` mismatches (13 files) pre-exist on develop and are unrelated. No `os.environ` usage anywhere in apps/backend | apps/backend/core/config.py | PHASE1-WEEK2-002: core/database.py async SQLAlchemy engine + session factory |
