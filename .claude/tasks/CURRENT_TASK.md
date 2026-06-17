# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-003
## TASK NAME: All ORM models — user, fine_tune_job, dataset, experiment, model_registry
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-003-orm-models

## OBJECTIVE
Create SQLAlchemy 2.0 async-compatible declarative ORM models for all six tables
(`users`, `datasets`, `fine_tune_jobs`, `experiments`, `experiment_runs`, `model_registry`)
under `apps/backend/models/`, each inheriting `Base` from `core/database.py`
(PHASE1-WEEK2-002). These models are the foundation for the Alembic initial migration
(PHASE1-WEEK2-004) and every service/route built afterward.

## ACCEPTANCE CRITERIA
- [ ] `models/user.py` — `User` model: id (UUID pk), email (unique), hashed_password,
      full_name, is_active, created_at, updated_at
- [ ] `models/dataset.py` — `Dataset` model: id, user_id (FK → users, cascade delete),
      name, format (alpaca/sharegpt/chatml), storage_path, size_bytes, row_count,
      quality_report (JSONB), created_at, updated_at; index `idx_datasets_user`
- [ ] `models/fine_tune_job.py` — `FineTuneJob` model: id, user_id (FK → users, cascade
      delete), dataset_id (FK → datasets, optional/nullable), status, base_model_id,
      methodology, training_config (JSONB), gpu_type, cloud_vendor, live metrics
      (train_loss, eval_loss, gpu_utilization_pct, vram_used_gb, tokens_per_second),
      estimated_cost_usd, actual_cost_usd, created_at, updated_at; indexes
      `idx_jobs_user_id`, `idx_jobs_status`
- [ ] `models/experiment.py` — `Experiment` model: id, user_id (FK → users, cascade
      delete), name, description, created_at, updated_at
- [ ] `models/experiment.py` (or separate file) — `ExperimentRun` model: id,
      experiment_id (FK → experiments), fine_tune_job_id (FK → fine_tune_jobs), metrics
      snapshot (JSONB), created_at
- [ ] `models/model_registry.py` — `ModelRegistry` model: id, user_id (FK → users,
      cascade delete), fine_tune_job_id (FK → fine_tune_jobs, optional/nullable), name,
      base_model_id, storage_path, hf_repo_id, gguf_export_path, vllm_endpoint,
      created_at, updated_at; index `idx_registry_user`
- [ ] All FKs to `users.id` use `ondelete="CASCADE"`
- [ ] All models import `Base` from `core.database` (no duplicate declarative bases)
- [ ] `models/__init__.py` imports every model class so Alembic autogenerate can see them
      via `Base.metadata`
- [ ] All primary keys are UUID (`sqlalchemy.dialects.postgresql.UUID` or
      `sqlalchemy.Uuid`), server-generated default
- [ ] `created_at`/`updated_at` use `server_default=func.now()` (and `onupdate=func.now()`
      for `updated_at` where applicable)
- [ ] `uv run python -c "from models import User, Dataset, FineTuneJob, Experiment, ExperimentRun, ModelRegistry"`
      imports without error
- [ ] `uv run ruff check .` and `uv run ruff format --check apps/backend/models/` pass
- [ ] No sync SQLAlchemy session usage; no `os.environ` direct access

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-003-orm-models
```

### Step 2 — Write ORM models
One file per table under `apps/backend/models/` (`user.py`, `dataset.py`,
`fine_tune_job.py`, `experiment.py`, `model_registry.py`), each defining a class that
inherits `Base` from `core.database`. Use `Mapped[...]` / `mapped_column(...)` typed
declarative style (SQLAlchemy 2.0), matching the schema in CLAUDE.md §4. Wire up
relationships (`relationship(...)`) where useful (e.g. `User.datasets`,
`FineTuneJob.dataset`, `Experiment.runs`) but keep them optional/lazy — don't
over-engineer cascades beyond what's specified. Re-export everything from
`models/__init__.py`.

### Step 3 — Verify
```
cd apps/backend
uv run python -c "from models import User, Dataset, FineTuneJob, Experiment, ExperimentRun, ModelRegistry"
uv run ruff check .
uv run ruff format --check models/
```

### Step 4 — Stage, commit, push
```
git add apps/backend/models/
git commit -m "feat(models): PHASE1-WEEK2-003 SQLAlchemy ORM models for all tables"
git push origin feat/PHASE1-WEEK2-003-orm-models
```

### Step 5 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-003
3. BACKLOG.md → PHASE1-WEEK2-003 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-004 content (Alembic initial migration)

## FILES TO UPDATE IN THIS TASK
- apps/backend/models/user.py
- apps/backend/models/dataset.py
- apps/backend/models/fine_tune_job.py
- apps/backend/models/experiment.py
- apps/backend/models/model_registry.py
- apps/backend/models/__init__.py

## BLOCKERS
None

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-004 (Alembic initial migration) runs
`alembic revision --autogenerate` against these models, so every table/column/index
named in the acceptance criteria above must actually exist on the classes — Alembic
autogenerate can only see what's imported into `Base.metadata` via `models/__init__.py`.
Continue down the Week 2 backlog in dependency order: config → database → ORM models →
alembic migration → security → auth → storage → celery_app → exceptions → main.py →
health → auth routes → seed_data. The celery_worker and celery_beat containers are still
restarting because `core/celery_app.py` doesn't exist yet (PHASE1-WEEK2-008 fixes that).

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-002)
Completed 2026-06-17. Created `apps/backend/core/database.py`: async engine via
`create_async_engine(settings.DATABASE_URL, echo=settings.ENVIRONMENT == "development",
pool_pre_ping=True)`, `AsyncSessionLocal = async_sessionmaker(bind=engine,
class_=AsyncSession, expire_on_commit=False)`, a `Base(DeclarativeBase)` for ORM models
to inherit, and an `async def get_db()` FastAPI dependency that yields a session and
closes it in a `finally` block. Verified the import line from the acceptance criteria
succeeds, `ruff check .` and `ruff format --check core/database.py` both pass. No
`os.environ` usage — DB URL pulled via `core.config.settings.DATABASE_URL` only.
Committed and pushed to feat/PHASE1-WEEK2-002-core-database; pre-commit hooks (ruff
lint/format backend) passed automatically on commit.
