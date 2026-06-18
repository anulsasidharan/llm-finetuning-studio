# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-004
## TASK NAME: Alembic config + initial migration
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-004-alembic-migration

## OBJECTIVE
Wire `migrations/env.py` up to the ORM models from PHASE1-WEEK2-003 (currently
`target_metadata = None`) and generate + apply the initial Alembic migration that
creates all six tables (`users`, `datasets`, `fine_tune_jobs`, `experiments`,
`experiment_runs`, `model_registry`) with their indexes and FKs against the running
Postgres container.

## ACCEPTANCE CRITERIA
- [ ] `migrations/env.py` imports `from models import Base` (or equivalent) and sets
      `target_metadata = Base.metadata` instead of `None`
- [ ] `migrations/env.py` import path resolves correctly under both `alembic` CLI
      invocation (cwd = `apps/backend`) and CI — verify `prepend_sys_path = .` in
      `alembic.ini` is sufficient, or adjust `sys.path` in `env.py` if not
- [ ] `uv run alembic revision --autogenerate -m "initial schema"` produces a migration
      under `migrations/versions/` containing `create_table` for all six tables, all
      columns from CLAUDE.md §4, all four named indexes (`idx_datasets_user`,
      `idx_jobs_user_id`, `idx_jobs_status`, `idx_registry_user`), and all FKs (cascade
      ones to `users.id` show `ondelete="CASCADE"` in the generated op)
- [ ] Generated migration reviewed by hand — no unwanted drops/renames, no missing
      autogenerate comments that hide real schema diffs
- [ ] `uv run alembic upgrade head` runs cleanly against the running `fts_postgres`
      container (`localhost:5433`) using `DATABASE_URL_SYNC`
- [ ] `uv run alembic downgrade base` then `uv run alembic upgrade head` both succeed
      (round-trip safety check)
- [ ] Confirm tables exist post-migration, e.g. via
      `docker exec fts_postgres psql -U fts_user -d fts_db -c "\dt"`
- [ ] `uv run ruff check .` and `uv run ruff format --check migrations/` pass (note:
      `migrations/*` has `E402, F401` ignored per `ruff.toml`)
- [ ] No sync SQLAlchemy session usage anywhere outside the Alembic migration runner
      itself (Alembic requires a sync engine internally — that's expected and fine)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-004-alembic-migration
```

### Step 2 — Wire env.py to models metadata
Edit `apps/backend/migrations/env.py`: replace `target_metadata = None` with an import
of `Base` from `models` (via `core.database`) and `target_metadata = Base.metadata`.
Confirm `models/__init__.py` (from PHASE1-WEEK2-003) already imports every model class,
so `Base.metadata` is fully populated at import time.

### Step 3 — Generate migration
```
cd apps/backend
uv run alembic revision --autogenerate -m "initial schema"
```
Review the generated file under `migrations/versions/` line by line against CLAUDE.md §4.

### Step 4 — Apply + verify
```
uv run alembic upgrade head
docker exec fts_postgres psql -U fts_user -d fts_db -c "\dt"
uv run alembic downgrade base
uv run alembic upgrade head
```

### Step 5 — Lint + format
```
uv run ruff check .
uv run ruff format --check migrations/
```

### Step 6 — Stage, commit, push
```
git add apps/backend/migrations/
git commit -m "feat(db): PHASE1-WEEK2-004 alembic initial migration"
git push origin feat/PHASE1-WEEK2-004-alembic-migration
```

### Step 7 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-004
3. BACKLOG.md → PHASE1-WEEK2-004 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-005 content (core/security.py)

## FILES TO UPDATE IN THIS TASK
- apps/backend/migrations/env.py
- apps/backend/migrations/versions/<new_revision>.py

## BLOCKERS
None — `fts_postgres` container must be running (`docker compose up -d postgres`) to
apply/verify the migration.

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-005 (`core/security.py` — bcrypt password hashing) can
start in parallel with PHASE1-WEEK2-007/008/009 since none of those depend on the ORM
models directly. Continue down the Week 2 backlog in dependency order: config →
database → ORM models → alembic migration → security → auth → storage → celery_app →
exceptions → main.py → health → auth routes → seed_data. The celery_worker and
celery_beat containers are still restarting because `core/celery_app.py` doesn't exist
yet (PHASE1-WEEK2-008 fixes that) — unrelated to this task.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-003)
Completed 2026-06-18. Wrote SQLAlchemy 2.0 typed declarative ORM models for all six
tables — `User`, `Dataset`, `FineTuneJob`, `Experiment`, `ExperimentRun`,
`ModelRegistry` — one file per table under `apps/backend/models/`, all inheriting
`Base` from `core.database`. UUID PKs via `postgresql.UUID(as_uuid=True)` with
`server_default=func.gen_random_uuid()`. JSONB for `training_config`/`quality_report`/
`metrics`. Cascade-delete FKs to `users.id`; optional FKs (`dataset_id` on
`FineTuneJob`, `fine_tune_job_id` on `ModelRegistry`) left as plain nullable FKs per
spec. Added the four named indexes via `index=True`. Bidirectional `relationship()`s
wired with `TYPE_CHECKING`-only imports to avoid circular imports between model files.
`models/__init__.py` re-exports every class so `Base.metadata` is fully populated on
import — this is what PHASE1-WEEK2-004 needs for `alembic revision --autogenerate` to
see the schema. Verified the import line from acceptance criteria succeeds, `ruff
check .` and `ruff format --check models/` both clean. Committed and pushed to
feat/PHASE1-WEEK2-003-orm-models; pre-commit hooks (ruff lint/format backend) passed
automatically on commit.
