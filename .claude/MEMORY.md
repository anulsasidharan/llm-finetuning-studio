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
- Last completed task: PHASE1-WEEK2-008 — core/celery_app.py Celery app + queue routing (2026-06-18)
- Next task: PHASE1-WEEK2-009 — core/exceptions.py custom exception hierarchy

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
- bcrypt MUST stay pinned to 4.0.1 in apps/backend/requirements.txt — passlib 1.7.4 (unmaintained) is incompatible with bcrypt>=4.1's stricter 72-byte enforcement (raises ValueError during passlib's internal self-test); do not bump bcrypt without also replacing passlib

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
| 2026-06-17 | PHASE1-WEEK2-002: Created `core/database.py` — async engine via `create_async_engine(settings.DATABASE_URL, echo=settings.ENVIRONMENT == "development", pool_pre_ping=True)`, `AsyncSessionLocal` (`async_sessionmaker`, `expire_on_commit=False`), declarative `Base(DeclarativeBase)`, and `get_db()` FastAPI dependency yielding an `AsyncSession` and closing it in `finally`. Verified import, `ruff check` and `ruff format --check` both clean. Pre-commit hooks (ruff lint/format on backend) passed automatically. Pushed branch; PR not opened (left for manual creation per established workflow) | apps/backend/core/database.py | PHASE1-WEEK2-003: all ORM models (user, fine_tune_job, dataset, experiment, model_registry) |
| 2026-06-18 | PHASE1-WEEK2-003: Wrote SQLAlchemy 2.0 typed declarative ORM models for all six tables — `User`, `Dataset`, `FineTuneJob`, `Experiment`, `ExperimentRun`, `ModelRegistry` — each in its own file under `apps/backend/models/`, all inheriting `Base` from `core.database`. UUID PKs via `postgresql.UUID(as_uuid=True)` with `server_default=func.gen_random_uuid()` (built into PG13+, no pgcrypto extension needed). JSONB for `training_config`/`quality_report`/`metrics`. All FKs to `users.id` use `ondelete="CASCADE"`; `dataset_id`/`fine_tune_job_id` optional FKs (on `FineTuneJob`/`ModelRegistry`) are plain nullable FKs without cascade per spec. Added the four named indexes (`idx_datasets_user`, `idx_jobs_user_id`, `idx_jobs_status`, `idx_registry_user`) via `index=True` on the respective columns. Wired bidirectional `relationship()`s using `TYPE_CHECKING`-only imports to avoid circular imports. `models/__init__.py` re-exports every class. Verified the exact import line from acceptance criteria succeeds, `ruff check .` and `ruff format --check models/` both clean (pre-commit hook also passed automatically on commit). Pushed branch; PR not opened (left for manual creation per established workflow) | apps/backend/models/{user,dataset,fine_tune_job,experiment,model_registry,__init__}.py | PHASE1-WEEK2-004: Alembic config + initial migration |
| 2026-06-18 | PHASE1-WEEK2-004: Wired `migrations/env.py` to ORM metadata — `from core.database import Base` + explicit import of all six model classes from `models` (so `Base.metadata` is fully populated), `target_metadata = Base.metadata` replacing `None`. Found PHASE1-WEEK2-003's claim that `index=True` produced the four spec-named indexes was wrong — plain `index=True` autogenerates SQLAlchemy default names (`ix_<table>_<column>`), not `idx_datasets_user`/`idx_jobs_user_id`/`idx_jobs_status`/`idx_registry_user`. Fixed by replacing `index=True` with explicit `Index("idx_...", "column")` entries in `__table_args__` on `Dataset`, `FineTuneJob` (two indexes: user_id + status), and `ModelRegistry`. Ran `uv run alembic revision --autogenerate -m "initial schema"` from `apps/backend` with `DATABASE_URL_SYNC=postgresql://fts_user:fts_dev_password_2024@localhost:5433/fts_db` (note: `.env`'s `DATABASE_URL_SYNC` uses Docker-internal host `postgres:5432`, not reachable from the host — must override when running alembic outside Docker) → generated `migrations/versions/c631a2aed670_initial_schema.py` with all 6 `create_table`s, all 4 named indexes, and correct `ondelete="CASCADE"` FKs. Reviewed by hand — no unwanted drops/renames (first migration). Applied `alembic upgrade head`, confirmed via `docker exec fts_postgres psql -c "\dt"` and `"\di"` that all 7 relations (6 tables + alembic_version) and all 4 named indexes exist. Verified `downgrade base` → `upgrade head` round-trip succeeds cleanly. `ruff check .` and `ruff format --check migrations/` both clean after auto-fixing import sort + trailing whitespace in the generated file (these rules are NOT in the `migrations/*` per-file-ignore list — only `E402`/`F401` are ignored there). Backend test suite (2 tests) still passes. Pushed branch; PR not opened (left for manual creation per established workflow). **Gotcha discovered:** the Bash tool's cwd persists across calls within a session — using `cd apps/backend && cmd` directly (not in a subshell) leaks the cwd change forward and breaks the `.claude/hooks/lint.py` PostToolUse hook (it resolves paths relative to cwd). Always wrap `cd`-then-run sequences in a subshell `(cd dir && cmd)` to keep the outer shell at repo root | apps/backend/migrations/env.py, apps/backend/migrations/versions/c631a2aed670_initial_schema.py, apps/backend/models/{dataset,fine_tune_job,model_registry}.py | PHASE1-WEEK2-005: core/security.py bcrypt password hashing |
| 2026-06-18 | PHASE1-WEEK2-005: Created `core/security.py` — `pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")`, `hash_password(password: str) -> str`, `verify_password(plain_password: str, hashed_password: str) -> bool`, exactly per spec. Hit a real bug while running the new tests (not flaky): passlib 1.7.4 (unmaintained since 2020) is incompatible with bcrypt>=4.1 — passlib's internal backend self-test (`detect_wrap_bug`) hashes a 72+ byte secret on first use, and bcrypt 4.1+ raises `ValueError: password cannot be longer than 72 bytes` instead of bcrypt's old silent-truncate behavior. `requirements.txt` had `bcrypt==5.0.0` pinned, tripping this on every call. Fixed by pinning `bcrypt==4.0.1` (last version confirmed compatible with passlib's self-test) and reinstalling via `uv pip install -r requirements.txt`. Added 3 unit tests in `tests/test_security.py` (hash differs from input, verify succeeds on correct password, verify fails on wrong password) — full suite now 5/5 passing. `ruff check .` clean; `ruff format --check core/ tests/` flagged 5 pre-existing unformatted files unrelated to this task (`core/__init__.py`, `core/config.py`, `core/database.py`, `tests/conftest.py`, `tests/test_health.py` — consistent with the 13-file pre-existing mismatch noted in PHASE1-WEEK2-001); the 2 new files are clean. Pre-commit hook passed automatically. Pushed branch; PR not opened (manual creation per established workflow). **Gotcha repeated:** a bare `cd apps/backend && cmd` (no subshell parens) leaked cwd forward again and broke the next Edit's lint hook — had to manually `cd` back to repo root. Reinforces: always use `(cd dir && cmd)` | apps/backend/core/security.py, apps/backend/tests/test_security.py, apps/backend/requirements.txt (bcrypt 5.0.0 → 4.0.1) | PHASE1-WEEK2-006: core/auth.py JWT create/verify + get_current_user dependency |
| 2026-06-18 | PHASE1-WEEK2-006: Created `core/auth.py` — `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`, `create_access_token`/`create_refresh_token` via `jose.jwt.encode` against `settings.SECRET_KEY`/`settings.ALGORITHM` (expiry from `settings.ACCESS_TOKEN_EXPIRE_MINUTES`/`settings.REFRESH_TOKEN_EXPIRE_DAYS`), `decode_token` via `jose.jwt.decode` catching `JWTError` and re-raising a shared `CREDENTIALS_EXCEPTION = HTTPException(401)` (no `core/exceptions.py` yet — deferred to PHASE1-WEEK2-009), and `get_current_user` (`Depends(oauth2_scheme)` + `Depends(get_db)`) resolving the `sub` claim to a UUID and loading the `User` via `db.scalar(select(User).where(...))`, raising 401 on any failure. Added 5 unit tests in `tests/test_auth.py` (access + refresh round-trip, expired token raises 401, tampered token raises 401, wrong-signature token raises 401) — full suite now 10/10 passing. `ruff check .` clean; `ruff format --check core/ tests/` flagged 7 pre-existing unformatted files unrelated to this task (`core/__init__.py`, `core/config.py`, `core/database.py`, `core/security.py`, `tests/conftest.py`, `tests/test_health.py`, `tests/test_security.py` — grew from the 5 noted in PHASE1-WEEK2-005, but confirmed via `git status`/`git diff` that none were touched this session, so the drift is pre-existing on develop); the 2 new files are clean. Pre-commit hook passed automatically. Pushed branch; PR not opened (manual creation per established workflow). **New gotcha:** the PostToolUse lint/format hook runs after *every* Edit/Write call individually — adding an import in one `Edit` and its only usage in a later, separate `Edit` let the hook's ruff auto-fix strip the import as "unused" in between; had to re-add it. Prefer making the import + its first usage in the same tool call, or verify the file afterward | apps/backend/core/auth.py, apps/backend/tests/test_auth.py | PHASE1-WEEK2-007: core/storage.py MinIO client wrapper |
| 2026-06-18 | PHASE1-WEEK2-007: Created `core/storage.py` — module-level `minio_client = Minio(f"{settings.MINIO_HOST}:{settings.MINIO_PORT}", access_key=settings.MINIO_ROOT_USER, secret_key=settings.MINIO_ROOT_PASSWORD, secure=settings.MINIO_USE_SSL)` built once at import time, plus thin wrappers `upload_file`/`download_file`/`get_presigned_url`/`delete_file` calling `put_object`/`get_object`/`presigned_get_object`/`remove_object` respectively (verified exact signatures against installed `minio==7.2.7` via `inspect.signature` before writing — `presigned_get_object` takes `expires: timedelta`, not raw seconds, so `get_presigned_url` converts `expires_seconds` via `timedelta(seconds=...)`; `get_object` returns a `BaseHTTPResponse` that must be `.read()` then `.close()` + `.release_conn()`'d, done in a `try/finally`). No bucket names hardcoded in the module — callers pass one of the four `Settings` bucket constants. Added 4 unit tests in `tests/test_storage.py`, all mocking `core.storage.minio_client` via `unittest.mock.patch` (no live MinIO needed) — full suite now 14/14 passing. `ruff check .` clean; `ruff format --check core/storage.py tests/test_storage.py` clean (had one line-length wrap needed on the `get_presigned_url` return statement, fixed immediately). Pre-commit hook passed automatically. Pushed branch; PR not opened (manual creation per established workflow). **Gotcha repeated:** ran the `minio` signature-inspection command with a bare `cd apps/backend && ...` (no subshell), which leaked cwd forward and broke the next `Write`'s PostToolUse lint hook (`lint.py` not found relative to the leaked cwd) — confirmed file content was still correct via `Read`, then ran a plain `cd` back to repo root to recover; reinforces the standing rule to always wrap `cd`-then-run in `(cd dir && cmd)` | apps/backend/core/storage.py, apps/backend/tests/test_storage.py | PHASE1-WEEK2-008: core/celery_app.py Celery app + queue routing |
| 2026-06-18 | PHASE1-WEEK2-008: Created `core/celery_app.py` — module-level `celery = Celery("fts", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)` (verified against installed `celery==5.4.0`), `celery.conf.update(task_serializer="json", result_serializer="json", accept_content=["json"], timezone="UTC", enable_utc=True, task_routes={"tasks.training_tasks.*": {"queue": "training"}, "tasks.export_tasks.*": {"queue": "export"}}, task_default_queue="default")` — matches the `--queues=training,export,default` flag already in `docker-compose.yml`'s `celery_worker` command without changing it. Added 4 config-only unit tests in `tests/test_celery_app.py` (app name, broker/backend resolve from settings, serialization defaults, task_routes mapping) — full suite now 18/18 passing. `ruff check .` and `ruff format --check core/celery_app.py tests/test_celery_app.py` both clean. **Real bug found + fixed (required by this task's acceptance criteria to verify containers recover):** brought up `celery_worker`/`celery_beat` via `docker compose up -d` and found `celery_beat` still restart-looping after adding `celery_app.py` — root cause was `core/config.py`'s `REPO_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"` raising `IndexError` inside the container, since `core/config.py` resolves to `/app/core/config.py` there (only 2 parent levels above `/`) vs `apps/backend/core/config.py` locally (4 levels to repo root) — this pre-existing PHASE1-WEEK2-001 bug, not the missing module, was the actual restart-loop cause all along. Fixed with a length guard: `_CONFIG_PARENTS = Path(__file__).resolve().parents; REPO_ROOT_ENV_FILE = _CONFIG_PARENTS[3] / ".env" if len(_CONFIG_PARENTS) > 3 else None` — safe because containers already get every var via docker-compose's `env_file: .env` directive injected straight into the container env, so the in-container `.env` *file* lookup is redundant and just needs to not crash. Verified locally (18/18 tests still pass) and in Docker (`docker compose restart celery_worker celery_beat` → both `Up` after 15s+, not `Restarting`; worker log shows clean `Connected to redis://...` + `celery@... ready`). Also gitignored `celerybeat-schedule` (celery beat's runtime sqlite artifact written to `apps/backend/` on startup). Two commits pushed: the celery_app feature commit + a separate `fix(config): ...` commit for the guard. Pushed `feat/PHASE1-WEEK2-008-celery-app`; PR not opened (manual creation per established workflow). **Gotcha repeated a fourth time:** a bare `cd apps/backend && uv run python -c "import celery; ..."` (Bash tool, no subshell parens) leaked cwd forward exactly as before — caught immediately via `pwd` before the next Write and recovered with a plain `cd` back to repo root; treat `(cd dir && cmd)` as fully non-negotiable even for one-line version checks | apps/backend/core/celery_app.py, apps/backend/tests/test_celery_app.py, apps/backend/core/config.py (IndexError guard), .gitignore (celerybeat-schedule) | PHASE1-WEEK2-009: core/exceptions.py custom exception hierarchy |
