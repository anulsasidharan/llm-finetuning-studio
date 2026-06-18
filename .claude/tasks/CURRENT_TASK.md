# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-006
## TASK NAME: core/auth.py — JWT create + verify + get_current_user dependency
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-006-core-auth

## OBJECTIVE
Create `apps/backend/core/auth.py` with JWT access/refresh token creation and
verification (via `python-jose`), plus a FastAPI `get_current_user` dependency
that resolves the authenticated `User` from a bearer token. Depends on
`core/security.py` (PHASE1-WEEK2-005, done) for password verification and on
`core/config.py`'s `Settings` for `SECRET_KEY`, `ALGORITHM`,
`ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`.

## ACCEPTANCE CRITERIA
- [ ] `create_access_token(data: dict, expires_delta: timedelta | None = None) -> str`
- [ ] `create_refresh_token(data: dict) -> str`
- [ ] `decode_token(token: str) -> dict` — raises on invalid/expired token
- [ ] `get_current_user` — FastAPI dependency (`Depends(oauth2_scheme)` +
      `Depends(get_db)`) that decodes the bearer token, loads the `User` by id
      from the DB async session, and raises `401` if missing/invalid
- [ ] All values (`SECRET_KEY`, `ALGORITHM`, expiry settings) read from
      `core.config.settings` — never hardcoded
- [ ] Full type hints on every function signature (CLAUDE.md §6)
- [ ] No `print()` calls — use `structlog` only if logging is genuinely needed
- [ ] Unit tests under `apps/backend/tests/test_auth.py` covering: access token
      round-trips (create → decode → same payload), expired token raises,
      tampered/invalid token raises
- [ ] `uv run pytest -q` passes (existing 5 tests + new auth tests)
- [ ] `uv run ruff check .` and `uv run ruff format --check core/ tests/` pass
      (note: `core/` already has 3 pre-existing format mismatches unrelated to
      this task — see SESSION LOG 2026-06-18 PHASE1-WEEK2-005; don't let that
      block on files you didn't touch, just keep your new/edited files clean)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-006-core-auth
```

### Step 2 — Write core/auth.py
- `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`
- `create_access_token` / `create_refresh_token` using `jose.jwt.encode` with
  `settings.SECRET_KEY`, `settings.ALGORITHM`; embed `exp` claim computed from
  `settings.ACCESS_TOKEN_EXPIRE_MINUTES` / `settings.REFRESH_TOKEN_EXPIRE_DAYS`
- `decode_token` using `jose.jwt.decode`, catching `JWTError` and re-raising as
  an appropriate exception (check if `core/exceptions.py` exists yet — it
  doesn't, PHASE1-WEEK2-009 — so raise `fastapi.HTTPException(401)` directly
  for now)
- `get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User`

### Step 3 — Write tests/test_auth.py
Cover the cases listed in acceptance criteria. Use `freezegun` or manual
`timedelta(seconds=-1)` expiry to test expired-token behavior without sleeping.

### Step 4 — Verify
```
(cd apps/backend && uv run pytest -q)
(cd apps/backend && uv run ruff check .)
(cd apps/backend && uv run ruff format --check core/ tests/)
```
(Remember: wrap `cd`-then-run sequences in a subshell so the outer shell's cwd
stays at repo root — otherwise the `.claude/hooks/lint.py` PostToolUse hook
breaks on the next Edit.)

### Step 5 — Stage, commit, push
```
git add apps/backend/core/auth.py apps/backend/tests/test_auth.py
git commit -m "feat(auth): PHASE1-WEEK2-006 JWT create/verify + get_current_user"
git push origin feat/PHASE1-WEEK2-006-core-auth
```

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-006
3. BACKLOG.md → PHASE1-WEEK2-006 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-007 content (core/storage.py)

## FILES TO UPDATE IN THIS TASK
- apps/backend/core/auth.py
- apps/backend/tests/test_auth.py

## BLOCKERS
None.

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-007 (`core/storage.py` — MinIO client wrapper)
and PHASE1-WEEK2-008 (`core/celery_app.py`) both only depend on
PHASE1-WEEK2-001 (`core/config.py`, done) and can be done in either order.
PHASE1-WEEK2-010 (`main.py` FastAPI app factory) depends on this task's
`core/auth.py` being in place. Continue down the Week 2 backlog in dependency
order: auth → storage → celery_app → exceptions → main.py → health → auth
routes → seed_data. The celery_worker and celery_beat containers are still
restarting because `core/celery_app.py` doesn't exist yet (PHASE1-WEEK2-008
fixes that) — unrelated to this task.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-005)
Completed 2026-06-18. Created `core/security.py` with a `passlib.CryptContext`
configured `schemes=["bcrypt"], deprecated="auto"`, plus `hash_password` and
`verify_password` pure functions (exact signatures from the original task
spec). While running the new tests, hit a real bug, not a flaky test: passlib
1.7.4 (unmaintained since 2020) is incompatible with bcrypt>=4.1 — passlib's
internal backend self-test (`detect_wrap_bug`) hashes a 72+ byte secret during
its first call, and bcrypt 4.1+ raises `ValueError: password cannot be longer
than 72 bytes` instead of the old silent-truncate behavior passlib expects.
The project's `requirements.txt` had `bcrypt==5.0.0` pinned, which trips this
every time. Fixed by pinning `bcrypt==4.0.1` (last version confirmed
compatible with passlib's self-test) and reinstalling via
`uv pip install -r requirements.txt`. All 3 new unit tests + the 2 pre-existing
health tests pass (5/5). `ruff check .` clean; `ruff format --check core/
tests/` flagged 5 pre-existing files (`core/__init__.py`, `core/config.py`,
`core/database.py`, `tests/conftest.py`, `tests/test_health.py`) that were
already unformatted before this session (consistent with the PHASE1-WEEK2-001
finding that 13 such files pre-exist on develop) — the 2 new files
(`core/security.py`, `tests/test_security.py`) are clean. Pre-commit hook
(ruff lint + format on backend) passed automatically. Pushed
`feat/PHASE1-WEEK2-005-core-security`; PR not opened (manual creation per
established workflow).

**Gotcha repeated this session:** running `(cd apps/backend && uv run ...)` in
a subshell is safe, but a plain `cd apps/backend && pytest` (no parens) in an
earlier turn left the Bash tool's cwd at `apps/backend`, which broke the next
Edit's PostToolUse lint hook (it resolves `.claude/hooks/lint.py` relative to
cwd). Had to explicitly `cd` back to repo root before the hook worked again.
Always use the `(cd dir && cmd)` subshell form — never a bare `cd dir && cmd`.
