# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-013
## TASK NAME: scripts/seed_data.py — model catalog + GPU pricing
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-013-seed-data

## OBJECTIVE
Per CLAUDE.md section 8 (Week 2 checklist) and the base-model catalog in
section "BASE MODELS IN CATALOG" of MEMORY.md, write
`apps/backend/scripts/seed_data.py` — a one-shot script that seeds the
base-model catalog and GPU pricing reference data so the rest of the app
(methodology selector, GPU selector, cost forecaster) has something to
read from. Depends on the Alembic migration (PHASE1-WEEK2-004, done) for
schema, but the catalog/pricing data itself is NOT yet modeled as ORM
tables — check CLAUDE.md section 4 (DATABASE SCHEMA) first: only
`users`, `datasets`, `fine_tune_jobs`, `experiments`, `experiment_runs`,
`model_registry` exist. There is no `model_catalog` or `gpu_pricing`
table yet.

## FIRST STEP — RESOLVE THIS BEFORE WRITING CODE
Confirm with the user (or by reading any newer planning notes) whether:
(a) catalog/pricing data should live in new DB tables (requiring new ORM
models + a migration — bigger scope than "seed script"), or
(b) catalog/pricing data is meant to be static, code-defined data (e.g.
`training_engine/config/model_catalog.py` already referenced in
CLAUDE.md's directory structure under `training_engine/`) and
`seed_data.py` just needs to exist as a no-op placeholder / future hook.
The CLAUDE.md directory tree lists `training_engine/config/model_catalog.py`
as a separate file from any backend seed script — read that file (if it
exists yet) before assuming seed_data.py needs to duplicate it.

## ACCEPTANCE CRITERIA (DRAFT — confirm scope first per above)
- [ ] `apps/backend/scripts/seed_data.py` exists and is runnable via
      `uv run python scripts/seed_data.py`
- [ ] Seeds the 12 base models from CLAUDE.md's catalog (Llama-3-8B/70B,
      Llama-3-8B-Instruct, Mistral-7B-v0.3/Instruct-v0.3, Phi-3-mini/medium,
      Qwen2-7B/72B, Gemma-2-9b/27b, CodeLlama-7b/34b) — exact storage
      location depends on the scope decision above
- [ ] Seeds GPU pricing reference data for at least the vendors in
      CLAUDE.md (AWS, GCP, Azure, RunPod, Lambda Labs)
- [ ] Idempotent — running it twice doesn't create duplicates or error
- [ ] Full type hints; no `print()` — use `structlog` for progress output
- [ ] `uv run pytest -q` still passes (full suite)
- [ ] `uv run ruff check .` and `uv run ruff format --check` pass on
      touched files

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-013-seed-data
```

### Step 2 — Resolve scope (see FIRST STEP above) before writing any code

### Step 3 — Implement seed script (shape depends on Step 2's answer)

### Step 4 — Verify
```
(cd apps/backend && uv run pytest -q)
(cd apps/backend && uv run ruff check .)
(cd apps/backend && uv run ruff format --check scripts/)
```
(Standing rule: always wrap `cd`-then-run sequences in a subshell
`(cd dir && cmd)` — applies to ANY directory navigation in the Bash tool,
not just verification commands.)

### Step 5 — Stage, commit, push
```
git add apps/backend/scripts/seed_data.py
git commit -m "feat(scripts): PHASE1-WEEK2-013 seed_data.py — model catalog + GPU pricing"
git push origin feat/PHASE1-WEEK2-013-seed-data
```

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-013
3. BACKLOG.md → PHASE1-WEEK2-013 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with the next Week 3 task
   (PHASE1-WEEK3-001 — Dataset ORM service + upload endpoint, or
   whichever Week 2 item remains, per BACKLOG.md)

## BLOCKERS
None outright, but the scope ambiguity above (DB tables vs. static
config) should be resolved before writing code — don't guess silently.

## NOTES FOR NEXT TASK
After this task, Week 2's backlog is fully closed out
(PHASE1-WEEK2-001 through 013 all done) and Week 3 begins: dataset
upload + frontend shell (see BACKLOG.md's Week 3 section).

Still open from PHASE1-WEEK2-009 (optional, low priority): `core/auth.py`'s
local `CREDENTIALS_EXCEPTION = HTTPException(401)` could be migrated to
the `core/exceptions.py` `UnauthorizedError` hierarchy now that both the
hierarchy and its FastAPI exception handler exist (added in
PHASE1-WEEK2-012) — not a hard requirement, just consistency cleanup.

Known unrelated issue (not in scope, just flagged): `fts_backend`'s
Docker `start.sh` fails with `set: Illegal option -` on container start
in this environment — looks like a CRLF line-ending issue from a Windows
checkout corrupting a `set -euo pipefail` (or similar) line. Verification
has been worked around by running the app locally via `uv run uvicorn`
against host-mapped ports instead of inside the `fts_backend` container.
Worth a dedicated fix-it task at some point.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-012)
Completed 2026-06-18. Created `schemas/auth.py` and
`api/v1/routes/auth.py` wiring `POST /register` (409 on duplicate email),
`POST /login` (401 on bad credentials, issues access+refresh tokens),
`POST /refresh` (re-validates the user still exists, issues a new token
pair), `GET /me`, and — after confirming scope with the user — `POST
/logout` as a stateless 204 no-op. Wired `auth.router` into
`api/v1/api_router`.

Found and fixed two real gaps while building this:
1. `core/exceptions.py`'s `AppException` hierarchy was never connected to
   FastAPI — added an `@app.exception_handler(AppException)` in
   `main.py` so `ConflictError`/`UnauthorizedError` actually return their
   declared status codes instead of an unhandled 500.
2. `tests/conftest.py`'s `client` fixture was function-scoped, giving
   each test its own event loop while the async DB engine/pool is a
   process-wide singleton — connections leaked across loops and crashed
   on Windows+asyncpg. Fixed by making `client` session-scoped.

Added 13 tests in `tests/test_auth_routes.py` that hit the routes for
real against the live dev Postgres (no mocking), using `/register` for
setup and sync `psycopg2` for cleanup. Verified locally with
`DATABASE_URL`/`DATABASE_URL_SYNC` overridden to `localhost:5433`,
matching exactly what CI's `backend-test` job already does. Full suite
47/47 passing. `ruff check .` and `ruff format --check` clean on all
touched files. Pushed `feat/PHASE1-WEEK2-012-auth-routes` (2 commits); PR
not opened (manual creation per established workflow).
