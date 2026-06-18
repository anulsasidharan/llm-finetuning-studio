# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-010
## TASK NAME: main.py — FastAPI app factory + router registration + CORS
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-010-fastapi-app

## OBJECTIVE
Turn `apps/backend/main.py` into a proper FastAPI app factory: CORS
middleware, the existing `/health` startup wiring, and a place for routers
to be registered as routes get built (auth routes land next in
PHASE1-WEEK2-012, so the router registration pattern should be ready for
that, even though no route modules exist yet beyond whatever `main.py`
currently has).

## ACCEPTANCE CRITERIA
- [ ] Read the current `apps/backend/main.py` first — it already has a
      `@app.on_event("startup")` (flagged as deprecated in pytest warnings
      during PHASE1-WEEK2-009 verification). Decide whether migrating it to
      a `lifespan` context manager belongs in this task (it touches the
      same file) or should be deferred — use judgment, but don't expand
      scope silently; mention the decision in the session log either way.
- [ ] `create_app() -> FastAPI` factory (or equivalent app-creation pattern
      consistent with what's already there)
- [ ] CORS middleware configured from `core/config.py` settings (check
      whether a CORS origins setting already exists in `Settings`; add one
      if not, following the existing pydantic-settings pattern)
- [ ] Router registration scaffold under `/api/v1` prefix per CLAUDE.md
      section 5 routes table — only wire routers that actually exist; leave
      clear structure for routers added in later tasks (auth in
      PHASE1-WEEK2-012, etc.)
- [ ] Full type hints
- [ ] No `print()` calls — use `structlog` if logging is needed
- [ ] Existing tests (`tests/test_health.py` and the full 33-test suite)
      still pass
- [ ] `uv run pytest -q` passes
- [ ] `uv run ruff check .` and `uv run ruff format --check core/ tests/
      main.py` pass on touched files (pre-existing format drift on
      untouched files is OK — see SESSION LOG 2026-06-18 entries)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-010-fastapi-app
```

### Step 2 — Read current main.py + core/config.py
Understand what's already wired (health check, startup event) before
changing anything.

### Step 3 — Implement app factory + CORS + router scaffold
Keep changes scoped to what's needed for this task; don't pull in routes
that don't exist yet.

### Step 4 — Verify
```
(cd apps/backend && uv run pytest -q)
(cd apps/backend && uv run ruff check .)
(cd apps/backend && uv run ruff format --check core/ tests/ main.py)
```
(Always wrap `cd`-then-run sequences in a subshell `(cd dir && cmd)` — a
bare `cd apps/backend && cmd` leaks the cwd forward in this Bash tool and
breaks the next Edit/Write's PostToolUse lint hook. This has now bitten
every session in Week 2.)

### Step 5 — Stage, commit, push
```
git add apps/backend/main.py apps/backend/core/config.py  # (if CORS setting added)
git commit -m "feat(api): PHASE1-WEEK2-010 FastAPI app factory + CORS + router scaffold"
git push origin feat/PHASE1-WEEK2-010-fastapi-app
```

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-010
3. BACKLOG.md → PHASE1-WEEK2-010 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-011 content (GET /health
   endpoint — note: a basic health check may already exist; this task is
   about meeting the full CLAUDE.md spec of database + redis + storage
   status)

## FILES TO UPDATE IN THIS TASK
- apps/backend/main.py
- apps/backend/core/config.py (only if a CORS origins setting needs adding)

## BLOCKERS
None.

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-011 (`GET /health` returning database +
redis + storage status per CLAUDE.md section 5) depends on `core/database.py`
(done), `core/storage.py` (done), and Redis connectivity. Then auth routes
(PHASE1-WEEK2-012) depend on `core/auth.py` (done) + the router scaffold
from this task. Then `scripts/seed_data.py` (PHASE1-WEEK2-013). Continue
down the Week 2 backlog in dependency order.

Also flagged in PHASE1-WEEK2-009: `core/auth.py`'s local
`CREDENTIALS_EXCEPTION = HTTPException(401)` could be migrated to the new
`core/exceptions.py` `UnauthorizedError` hierarchy now that it exists — not
required for this task, consider as a small follow-up when auth routes are
touched in PHASE1-WEEK2-012.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-009)
Completed 2026-06-18. Created `apps/backend/core/exceptions.py` —
framework-agnostic `AppException(Exception)` base with `status_code: int`
and `detail: str` set via `__init__(detail: str | None = None)`, falling
back to the class-level default `detail` when not overridden. Five concrete
subclasses: `NotFoundError` (404), `UnauthorizedError` (401),
`ForbiddenError` (403), `ConflictError` (409), `ValidationError` (422), each
with a sensible default `detail` message. No FastAPI import anywhere in the
module — keeps it safe to raise from `core/`, `services/`, or
`training_engine/`; translation to `HTTPException` is left for
routes/middleware at the API boundary (not built yet).

Added 15 parametrized unit tests in `tests/test_exceptions.py` (default
`status_code` per subclass, `detail` override via constructor, `isinstance`
check against `AppException`) — full suite now 33/33 passing. `uv run ruff
check .` clean; `uv run ruff format --check core/exceptions.py
tests/test_exceptions.py` clean (formatter ran automatically via the
PostToolUse hook on `Write`, no manual fixes needed). Pre-commit hook
(ruff lint/format on backend) passed automatically on commit. Pushed
`feat/PHASE1-WEEK2-009-exceptions` to origin; PR not opened (manual
creation per established workflow).

No new gotchas this session — followed the standing `(cd dir && cmd)`
subshell rule from the start and had no cwd leakage.
