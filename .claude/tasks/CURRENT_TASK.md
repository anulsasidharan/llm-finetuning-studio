# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-012
## TASK NAME: Auth routes — POST /register, /login, /refresh, GET /me
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-012-auth-routes

## OBJECTIVE
Per CLAUDE.md section 5, wire up the four auth endpoints:
`POST /api/v1/auth/register`, `POST /api/v1/auth/login`,
`POST /api/v1/auth/refresh`, `GET /api/v1/auth/me` (and `POST
/api/v1/auth/logout` is also listed in CLAUDE.md — confirm scope with
user before deferring it; logout is typically a no-op/client-side token
discard for stateless JWT, but check if a token-blocklist is expected).
All the underlying pieces already exist — this task is route wiring +
Pydantic schemas, not new core logic.

## ACCEPTANCE CRITERIA
- [ ] `apps/backend/schemas/auth.py` — `UserRegister` (email, password,
      full_name), `UserLogin` (email, password), `TokenResponse`
      (access_token, refresh_token, token_type), `RefreshRequest`
      (refresh_token), `UserResponse` (id, email, full_name, is_active,
      created_at) — Pydantic v2, full type hints
- [ ] `apps/backend/api/v1/routes/auth.py` — `router = APIRouter()` with:
  - `POST /register` — checks email uniqueness (409 `ConflictError` from
    `core/exceptions.py` if taken), hashes password via
    `core.security.hash_password`, creates `User` row, returns
    `UserResponse`
  - `POST /login` — looks up user by email, verifies password via
    `core.security.verify_password`, returns `TokenResponse` (access +
    refresh via `core.auth.create_access_token`/`create_refresh_token`)
  - `POST /refresh` — decodes the refresh token via `core.auth`, issues a
    new access token
  - `GET /me` — `Depends(core.auth.get_current_user)`, returns
    `UserResponse` for the current user
- [ ] Wire `auth.router` into `api/v1/__init__.py`'s `api_router` (the
  commented example is already there from PHASE1-WEEK2-010)
- [ ] All DB access async (`AsyncSession` via `Depends(get_db)`)
- [ ] Full type hints; no `print()`; `structlog` if logging needed
- [ ] New tests under `apps/backend/tests/` covering register (success +
  duplicate-email 409), login (success + wrong-password 401), refresh
  (success + invalid-token 401), me (success + unauthenticated 401)
- [ ] `uv run pytest -q` passes (full suite)
- [ ] `uv run ruff check .` and `uv run ruff format --check` pass on
  touched files

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-012-auth-routes
```

### Step 2 — Read core/auth.py, core/security.py, core/exceptions.py, models/user.py, api/v1/__init__.py
Confirm exact function signatures before wiring (don't assume — verify
`create_access_token`/`create_refresh_token`/`get_current_user`'s actual
params/return types).

### Step 3 — Implement schemas, then routes, then wire into api_router

### Step 4 — Verify
```
(cd apps/backend && uv run pytest -q)
(cd apps/backend && uv run ruff check .)
(cd apps/backend && uv run ruff format --check schemas/ api/ tests/)
```
(Standing rule: always wrap `cd`-then-run sequences in a subshell
`(cd dir && cmd)` — applies to ANY directory navigation in the Bash tool
this session, not just verification commands.)

### Step 5 — Stage, commit, push
```
git add apps/backend/schemas/auth.py apps/backend/api/v1/routes/auth.py apps/backend/api/v1/__init__.py apps/backend/tests/test_auth_routes.py
git commit -m "feat(api): PHASE1-WEEK2-012 auth routes — register/login/refresh/me"
git push origin feat/PHASE1-WEEK2-012-auth-routes
```

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-012
3. BACKLOG.md → PHASE1-WEEK2-012 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-013 content
   (`scripts/seed_data.py` — model catalog + GPU pricing, depends on
   Alembic migration from PHASE1-WEEK2-004, done)

## FILES TO UPDATE IN THIS TASK
- apps/backend/schemas/auth.py (new)
- apps/backend/api/v1/routes/auth.py (new)
- apps/backend/api/v1/__init__.py (uncomment + wire the auth router)
- apps/backend/tests/test_auth_routes.py (new)

## BLOCKERS
None — all dependencies (`core/auth.py`, `core/security.py`,
`core/exceptions.py`, `models/user.py`, `api/v1/api_router` scaffold) are
done.

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-013 (`scripts/seed_data.py` — model catalog
+ GPU pricing seed script, depends on the Alembic migration from
PHASE1-WEEK2-004). That closes out the remaining Week 2 backlog items
before Week 3 (dataset upload + frontend shell) begins.

Also still open from PHASE1-WEEK2-009: `core/auth.py`'s local
`CREDENTIALS_EXCEPTION = HTTPException(401)` could be migrated to the
`core/exceptions.py` `UnauthorizedError` hierarchy now that it exists —
worth doing in this task since auth.py is already being touched/extended
for routes, but not a hard requirement.

Known unrelated issue (not in scope, just flagged): `fts_backend`'s
Docker `start.sh` fails with `set: Illegal option -` on container start
in this environment — looks like a CRLF line-ending issue from a Windows
checkout corrupting a `set -euo pipefail` (or similar) line. Verification
in PHASE1-WEEK2-011 worked around it by running the app locally via `uv
run uvicorn` against host-mapped ports instead of inside the
`fts_backend` container. Worth a dedicated fix-it task at some point.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-011)
Completed 2026-06-18. Replaced `/health`'s static body with three
isolated dependency checks in `main.py`: `_check_database` (`SELECT 1`
via `AsyncSessionLocal`), `_check_redis` (`PING` via
`redis.asyncio.from_url(settings.REDIS_URL)`), `_check_storage`
(`asyncio.to_thread(minio_client.bucket_exists, settings.BUCKET_DATASETS)`).
Response now reports `database`/`redis`/`storage` as `"up"`/`"down"` plus
overall `status: "healthy"|"degraded"`.

Live verification against the real `fts_postgres`/`fts_redis`/`fts_minio`
containers (via host-mapped ports, since `.env` uses Docker-internal
hostnames) caught a real issue: when a dependency is unreachable, the
underlying client's default retry/backoff can block for 20s+ (measured
~20.5s for MinIO's `bucket_exists` on DNS failure) — bad for a
frequently-polled health endpoint. Fixed by wrapping each check in
`asyncio.wait_for(..., timeout=5.0)` via a new `_check_with_timeout`
helper; re-verified the endpoint now returns in ~6s reporting
`"degraded"` when a dependency is down.

Rewrote `tests/test_health.py` (7 tests). Full suite 37/37 passing (one
`test_auth.py` flaky test unrelated to this change, confirmed by
isolation rerun). `ruff check .` and `ruff format --check` clean on both
touched files. Pushed `feat/PHASE1-WEEK2-011-health-endpoint`; PR not
opened (manual creation per established workflow).
