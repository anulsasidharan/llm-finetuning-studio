# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-011
## TASK NAME: GET /health — database + redis + storage status
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-011-health-endpoint

## OBJECTIVE
The current `/health` endpoint in `apps/backend/main.py` only returns a
static `{"status": "healthy", "service": ..., "version": ...}` body. Per
CLAUDE.md section 5, `GET /health` must report actual database + redis +
storage connectivity status, not just a static "I'm up" response.

## ACCEPTANCE CRITERIA
- [ ] `/health` checks PostgreSQL connectivity (via `core/database.py`'s
      `AsyncSessionLocal`/`get_db()` — e.g. a trivial `SELECT 1`)
- [ ] `/health` checks Redis connectivity (a `PING` against
      `settings.REDIS_URL`)
- [ ] `/health` checks MinIO/storage connectivity (via
      `core/storage.py`'s `minio_client` — e.g. `bucket_exists` or
      equivalent lightweight call)
- [ ] Response body reports per-dependency status (e.g.
      `{"status": "healthy"|"degraded", "database": "up"|"down",
      "redis": "up"|"down", "storage": "up"|"down"}`) — exact shape is a
      judgment call, but it must surface all three independently
- [ ] Endpoint does not raise/500 when a dependency is down — catch and
      report `"down"` per-dependency, overall `status` reflects whether
      any dependency failed
- [ ] Full type hints
- [ ] No `print()` — use `structlog` if logging is needed
- [ ] Existing tests in `tests/test_health.py` updated for the new
      response shape; still passing
- [ ] `uv run pytest -q` passes (full suite)
- [ ] `uv run ruff check .` and `uv run ruff format --check core/ tests/
      main.py` pass on touched files

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-011-health-endpoint
```

### Step 2 — Read current main.py, core/database.py, core/storage.py, core/config.py (REDIS_URL)
Decide where the dependency-check logic lives — likely inline in
`main.py`'s `/health` handler (it's the only consumer so far), using
`get_db`/`AsyncSessionLocal`, a `redis.asyncio` client built from
`settings.REDIS_URL`, and `minio_client` from `core/storage.py`. Check
whether `redis` (the Python package) is already a dependency before
adding a new import.

### Step 3 — Implement
Keep each dependency check isolated (try/except per dependency) so one
failure doesn't mask the others or crash the endpoint.

### Step 4 — Verify
```
(cd apps/backend && uv run pytest -q)
(cd apps/backend && uv run ruff check .)
(cd apps/backend && uv run ruff format --check core/ tests/ main.py)
```
(Always wrap `cd`-then-run sequences in a subshell `(cd dir && cmd)` —
this now applies to ANY directory navigation in the Bash tool this
session, not just verification commands; a bare `cd .claude/tasks &&
ls` during tracking-file updates broke the lint hook in the
PHASE1-WEEK2-010 session.)

### Step 5 — Stage, commit, push
```
git add apps/backend/main.py apps/backend/tests/test_health.py  # + any new core/ file
git commit -m "feat(api): PHASE1-WEEK2-011 /health reports db + redis + storage status"
git push origin feat/PHASE1-WEEK2-011-health-endpoint
```

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-011
3. BACKLOG.md → PHASE1-WEEK2-011 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-012 content (auth routes:
   POST /register, /login, /refresh, GET /me — depends on `core/auth.py`
   (done), `core/security.py` (done), the router scaffold from
   PHASE1-WEEK2-010 (done))

## FILES TO UPDATE IN THIS TASK
- apps/backend/main.py
- apps/backend/tests/test_health.py
- apps/backend/requirements.txt (only if a new redis client dependency is needed)

## BLOCKERS
None.

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-012 (auth routes) depends on `core/auth.py`
(done), `core/security.py` (done), and the `api/v1/api_router` scaffold
from PHASE1-WEEK2-010 (done) — route modules go under
`apps/backend/api/v1/routes/`. Then `scripts/seed_data.py`
(PHASE1-WEEK2-013). Continue down the Week 2 backlog in dependency order.

Also flagged in PHASE1-WEEK2-009: `core/auth.py`'s local
`CREDENTIALS_EXCEPTION = HTTPException(401)` could be migrated to the
`core/exceptions.py` `UnauthorizedError` hierarchy now that it exists —
not required for this task, consider as a small follow-up when auth
routes are touched in PHASE1-WEEK2-012.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-010)
Completed 2026-06-18. Turned `apps/backend/main.py` into a
`create_app() -> FastAPI` factory (module-level `app = create_app()`
retained for `tests/conftest.py`'s `from main import app`). Migrated the
deprecated `@app.on_event("startup")` to an `@asynccontextmanager async
def lifespan(app)` — done in-task since it's the same file and was
producing a pytest deprecation warning. Added `Settings.CORS_ORIGINS:
list[str]` (default `["http://localhost:3000", "http://127.0.0.1:3000"]`)
so CORS middleware reads from config instead of a hardcoded list. Added
`api/v1/api_router = APIRouter()` in `apps/backend/api/v1/__init__.py` as
the router-registration scaffold (empty, with a commented example for
the auth router landing next), wired via `app.include_router(api_router,
prefix="/api/v1")`. `/health` endpoint body left unchanged — the full
CLAUDE.md spec (db/redis/storage status) is this task, PHASE1-WEEK2-011.

Full 33-test suite passes with zero warnings (deprecation warning gone).
`ruff check .` clean repo-wide; `ruff format --check` clean on all three
touched files. Pre-commit hook passed automatically. Pushed
`feat/PHASE1-WEEK2-010-fastapi-app`; PR not opened (manual creation per
established workflow).

**Gotcha, new flavor:** a bare `cd .claude/tasks && ls -la` (no subshell)
run while updating tracking files *after* the feature work was already
pushed leaked cwd forward and broke the next `Edit`'s lint hook. The
standing `(cd dir && cmd)` rule now applies to every directory
navigation in the Bash tool this session, not just verification commands
on `apps/backend`.
