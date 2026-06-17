# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-002
## TASK NAME: core/database.py — async SQLAlchemy engine + session factory
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-002-core-database

## OBJECTIVE
Create `apps/backend/core/database.py` with an async SQLAlchemy 2.0 engine (using
`settings.DATABASE_URL`), an async session factory, a declarative `Base`, and a FastAPI
`get_db` dependency that yields an `AsyncSession`. This is the foundation every ORM model
(PHASE1-WEEK2-003) and route depends on.

## ACCEPTANCE CRITERIA
- [ ] `core/database.py` creates an async engine via `create_async_engine(settings.DATABASE_URL, ...)`
- [ ] `AsyncSessionLocal` session factory (`async_sessionmaker`, `expire_on_commit=False`)
- [ ] Declarative `Base` (`DeclarativeBase` or `declarative_base()`) exported for ORM models to inherit
- [ ] `async def get_db() -> AsyncGenerator[AsyncSession, None]` dependency that yields a session
      and closes it in a `finally` block
- [ ] No sync SQLAlchemy sessions anywhere
- [ ] `uv run python -c "from core.database import engine, AsyncSessionLocal, Base, get_db"` imports
      without error
- [ ] `uv run ruff check .` and `uv run ruff format --check apps/backend/core/database.py` pass
- [ ] No `os.environ` direct access — must read DB URL via `core.config.settings`

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-002-core-database
```

### Step 2 — Write core/database.py
Use `sqlalchemy.ext.asyncio.create_async_engine`, `async_sessionmaker`, `AsyncSession`,
and `sqlalchemy.orm.DeclarativeBase`. Pull the connection string from
`core.config.settings.DATABASE_URL` (already typed and validated as of PHASE1-WEEK2-001).

### Step 3 — Verify
```
cd apps/backend
uv run python -c "from core.database import engine, AsyncSessionLocal, Base, get_db"
uv run ruff check .
uv run ruff format --check core/database.py
```

### Step 4 — Stage, commit, push
```
git add apps/backend/core/database.py
git commit -m "feat(database): PHASE1-WEEK2-002 async SQLAlchemy engine + session factory"
git push origin feat/PHASE1-WEEK2-002-core-database
```

### Step 5 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-002
3. BACKLOG.md → PHASE1-WEEK2-002 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-003 content (ORM models)

## FILES TO UPDATE IN THIS TASK
- apps/backend/core/database.py

## BLOCKERS
None

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-003 (all ORM models — user, fine_tune_job, dataset,
experiment, model_registry) depends directly on `Base` from this file. Continue down the
Week 2 backlog in dependency order: config → database → ORM models → alembic migration →
security → auth → storage → celery_app → exceptions → main.py → health → auth routes →
seed_data. The celery_worker and celery_beat containers are still restarting because
core/celery_app.py doesn't exist yet (PHASE1-WEEK2-008 fixes that).

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-001)
Completed 2026-06-17. Extended `apps/backend/core/config.py` so the `Settings` class covers
every backend-relevant variable in `.env.example` (App, Postgres, Redis, MinIO, AWS S3,
HuggingFace, Cloud GPU Vendors, GPU Pricing, Notifications, Training Engine), grouped with
section-header comments matching `.env.example`. Added `get_settings()` with `lru_cache`,
kept the module-level `settings` singleton for backward compatibility. Discovered the
original `env_file=".env"` was relative to cwd, which broke when running `uv run` from
`apps/backend` (no local `.env` there — only one at the repo root). Fixed by resolving the
`.env` path absolutely from `config.py`'s own location
(`Path(__file__).resolve().parents[3] / ".env"`), so it works regardless of invocation cwd
and matches how Docker Compose's `env_file: .env` already injects real env vars in
containers. Verified `uv run python -c "from core.config import settings; print(settings.APP_NAME)"`
succeeds, `ruff check .` passes clean, and confirmed (via `git stash`) that the 13 remaining
`ruff format` mismatches on develop are pre-existing and unrelated to this change — my edit
actually fixed config.py's own formatting. Confirmed no `os.environ` usage anywhere in
`apps/backend`. Committed and pushed to feat/PHASE1-WEEK2-001-core-config.
