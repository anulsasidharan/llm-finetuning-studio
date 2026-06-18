# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-005
## TASK NAME: core/security.py — bcrypt password hashing
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-005-core-security

## OBJECTIVE
Create `apps/backend/core/security.py` with password hashing/verification helpers
built on `passlib`'s bcrypt scheme. This is a standalone utility module — no JWT
logic here (that's PHASE1-WEEK2-006's `core/auth.py`, which depends on this module).

## ACCEPTANCE CRITERIA
- [ ] `core/security.py` defines a `passlib.context.CryptContext` configured with
      `schemes=["bcrypt"]`, `deprecated="auto"`
- [ ] `hash_password(password: str) -> str` — returns the bcrypt hash
- [ ] `verify_password(plain_password: str, hashed_password: str) -> bool` — returns
      whether the plaintext matches the hash
- [ ] Both functions have full type hints (per CLAUDE.md §6 convention)
- [ ] No `print()` calls; if logging is needed, use `structlog` (likely not needed for
      this module — it's pure functions)
- [ ] Add a quick unit test under `apps/backend/tests/` (e.g. `test_security.py`)
      covering: hash produces a different string than the input, verify succeeds on
      the correct password, verify fails on a wrong password
- [ ] `uv run pytest -q` passes (existing 2 tests + new security tests)
- [ ] `uv run ruff check .` and `uv run ruff format --check core/ tests/` pass

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-005-core-security
```

### Step 2 — Write core/security.py
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

### Step 3 — Write tests/test_security.py
Cover the three cases listed in acceptance criteria.

### Step 4 — Verify
```
cd apps/backend
uv run pytest -q
uv run ruff check .
uv run ruff format --check core/ tests/
```
(Remember: wrap `cd`-then-run sequences in a subshell — `(cd apps/backend && ...)` —
so the outer shell's cwd stays at repo root; otherwise the `.claude/hooks/lint.py`
PostToolUse hook breaks on the next Edit.)

### Step 5 — Stage, commit, push
```
git add apps/backend/core/security.py apps/backend/tests/test_security.py
git commit -m "feat(auth): PHASE1-WEEK2-005 bcrypt password hashing"
git push origin feat/PHASE1-WEEK2-005-core-security
```

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-005
3. BACKLOG.md → PHASE1-WEEK2-005 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-006 content (core/auth.py)

## FILES TO UPDATE IN THIS TASK
- apps/backend/core/security.py
- apps/backend/tests/test_security.py

## BLOCKERS
None.

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-006 (`core/auth.py` — JWT create + verify +
`get_current_user` FastAPI dependency) depends directly on this module's
`verify_password`/`hash_password`. `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
and `REFRESH_TOKEN_EXPIRE_DAYS` are already defined in `core/config.py`'s `Settings`
class — `core/auth.py` should read them from `settings`, never hardcode. `bcrypt`,
`passlib`, and `python-jose` are already pinned in `requirements.txt`. Continue down
the Week 2 backlog in dependency order: security → auth → storage → celery_app →
exceptions → main.py → health → auth routes → seed_data. The celery_worker and
celery_beat containers are still restarting because `core/celery_app.py` doesn't
exist yet (PHASE1-WEEK2-008 fixes that) — unrelated to this task.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-004)
Completed 2026-06-18. Wired `migrations/env.py` to ORM metadata
(`target_metadata = Base.metadata`, importing `core.database.Base` and all six model
classes from `models` so the metadata is fully populated). Discovered and fixed a
defect carried over from PHASE1-WEEK2-003: `index=True` on `Dataset.user_id`,
`FineTuneJob.user_id`/`status`, and `ModelRegistry.user_id` autogenerates default
SQLAlchemy index names (`ix_<table>_<column>`), not the spec names
(`idx_datasets_user`, `idx_jobs_user_id`, `idx_jobs_status`, `idx_registry_user`) —
replaced with explicit `Index(...)` entries in each model's `__table_args__`.
Generated `migrations/versions/c631a2aed670_initial_schema.py` via
`alembic revision --autogenerate`, reviewed by hand (all 6 `create_table`s, all 4
named indexes, correct `ondelete="CASCADE"` FKs, no unwanted drops since it's the
first migration). Applied `alembic upgrade head` against `fts_postgres`
(`localhost:5433`, overriding `DATABASE_URL_SYNC` since the `.env` value points at
the Docker-internal `postgres` host). Verified all 7 relations + 4 named indexes via
`psql \dt`/`\di`, and verified `downgrade base` → `upgrade head` round-trips cleanly.
`ruff check .` and `ruff format --check migrations/` both clean. Backend test suite
(2 tests) still passes. Pushed `feat/PHASE1-WEEK2-004-alembic-migration`; PR not
opened (manual creation per established workflow).
