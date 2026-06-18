# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-007
## TASK NAME: core/storage.py — MinIO client wrapper
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-007-core-storage

## OBJECTIVE
Create `apps/backend/core/storage.py` wrapping the `minio` Python SDK with a
single client instance plus upload/download/presigned-URL helpers, configured
entirely from `core.config.settings` (MinIO in dev → same interface works
against S3 in production per CLAUDE.md §1). Depends only on
`core/config.py` (PHASE1-WEEK2-001, done).

## ACCEPTANCE CRITERIA
- [ ] Module-level `minio_client = Minio(...)` built from `settings.MINIO_HOST`,
      `settings.MINIO_PORT` (combine as `f"{host}:{port}"`), `settings.MINIO_ROOT_USER`,
      `settings.MINIO_ROOT_PASSWORD`, `secure=settings.MINIO_USE_SSL`
- [ ] `upload_file(bucket: str, object_name: str, file_data: BinaryIO, length: int, content_type: str) -> None`
      using `minio_client.put_object`
- [ ] `download_file(bucket: str, object_name: str) -> bytes` using `minio_client.get_object`
      (read the response stream fully, then close + release per minio-py docs)
- [ ] `get_presigned_url(bucket: str, object_name: str, expires_seconds: int = 3600) -> str`
      using `minio_client.presigned_get_object` (note: takes a `timedelta`, not raw seconds —
      convert)
- [ ] `delete_file(bucket: str, object_name: str) -> None` using `minio_client.remove_object`
- [ ] The four bucket name constants already in `Settings`
      (`BUCKET_DATASETS`, `BUCKET_MODELS`, `BUCKET_CHECKPOINTS`, `BUCKET_EXPORTS` —
      see `core/config.py`) are the only bucket names callers should pass; don't
      hardcode bucket names inside `storage.py` itself
- [ ] Full type hints on every function signature (CLAUDE.md §6)
- [ ] No `print()` calls — use `structlog` only if logging is genuinely needed
- [ ] Unit tests under `apps/backend/tests/test_storage.py` — mock the `Minio`
      client (e.g. `unittest.mock.patch("core.storage.minio_client")`) since
      there's no live MinIO instance in the pytest environment; verify each
      wrapper function calls the underlying SDK method with the right args
- [ ] `uv run pytest -q` passes (existing 10 tests + new storage tests)
- [ ] `uv run ruff check .` and `uv run ruff format --check core/ tests/` pass
      on the files you touch (note: `core/__init__.py`, `core/config.py`,
      `core/database.py`, `core/security.py`, `tests/conftest.py`,
      `tests/test_health.py`, `tests/test_security.py` have pre-existing format
      drift unrelated to this task — see SESSION LOG 2026-06-18
      PHASE1-WEEK2-006 — don't let that block; just keep your new/edited files
      clean)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-007-core-storage
```

### Step 2 — Write core/storage.py
- Single `Minio` client built once at module import time from `settings`
- Thin wrapper functions per acceptance criteria — no bucket-creation logic
  here (buckets are created by the `minio_init` one-shot container in
  `docker-compose.yml`, already wired)
- Check the installed `minio` SDK version's exact method signatures before
  writing calls (`uv run python -c "import minio; print(minio.__version__)"`
  then check `put_object`/`get_object`/`presigned_get_object`/`remove_object`
  signatures) — don't guess

### Step 3 — Write tests/test_storage.py
Mock `core.storage.minio_client` and assert each wrapper calls through with
correct positional/keyword args. Don't require a live MinIO connection.

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
git add apps/backend/core/storage.py apps/backend/tests/test_storage.py
git commit -m "feat(storage): PHASE1-WEEK2-007 MinIO client wrapper"
git push origin feat/PHASE1-WEEK2-007-core-storage
```

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-007
3. BACKLOG.md → PHASE1-WEEK2-007 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-008 content (core/celery_app.py)

## FILES TO UPDATE IN THIS TASK
- apps/backend/core/storage.py
- apps/backend/tests/test_storage.py

## BLOCKERS
None.

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-008 (`core/celery_app.py`) also only depends on
PHASE1-WEEK2-001 and could have been done in either order relative to this
task. PHASE1-WEEK2-009 (`core/exceptions.py`) is next after that, then
PHASE1-WEEK2-010 (`main.py` FastAPI app factory, depends on auth from
PHASE1-WEEK2-006 — already done). Continue down the Week 2 backlog in
dependency order: storage → celery_app → exceptions → main.py → health → auth
routes → seed_data. The celery_worker and celery_beat containers are still
restarting because `core/celery_app.py` doesn't exist yet (PHASE1-WEEK2-008
fixes that) — unrelated to this task.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-006)
Completed 2026-06-18. Created `core/auth.py` — `oauth2_scheme =
OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`, `create_access_token`/
`create_refresh_token` (both via `jose.jwt.encode` against
`settings.SECRET_KEY`/`settings.ALGORITHM`, expiry from
`settings.ACCESS_TOKEN_EXPIRE_MINUTES`/`settings.REFRESH_TOKEN_EXPIRE_DAYS`),
`decode_token` (via `jose.jwt.decode`, catches `JWTError` and re-raises a
shared `CREDENTIALS_EXCEPTION` = `HTTPException(401)` — `core/exceptions.py`
doesn't exist yet, deferred to PHASE1-WEEK2-009), and `get_current_user`
(`Depends(oauth2_scheme)` + `Depends(get_db)`, decodes the token, looks up the
`sub` claim as a UUID, loads the `User` via `db.scalar(select(User).where(...))`,
raises 401 on any failure). Added 5 unit tests in `tests/test_auth.py`
(access + refresh token round-trip, expired token raises 401, tampered token
raises 401, wrong-signature token raises 401) — full suite now 10/10 passing.
`ruff check .` clean; `ruff format --check core/ tests/` flagged 7
pre-existing unformatted files unrelated to this task (`core/__init__.py`,
`core/config.py`, `core/database.py`, `core/security.py`, `tests/conftest.py`,
`tests/test_health.py`, `tests/test_security.py` — grew from the 5 noted in
PHASE1-WEEK2-005 to 7, but confirmed via `git status`/`git diff` that none of
these files were touched this session, so the drift is pre-existing on
`develop`, not introduced here); the 2 new files
(`core/auth.py`, `tests/test_auth.py`) are clean. Pre-commit hook (ruff lint +
format on backend) passed automatically. Pushed
`feat/PHASE1-WEEK2-006-core-auth`; PR not opened (manual creation per
established workflow).

**Gotcha this session:** the `.claude/hooks` PostToolUse formatter hook runs
*after every single Edit/Write call*, not just at the end. Adding an import
in one `Edit` call and its only usage in a separate, later `Edit` call let the
hook's ruff auto-fix strip the "unused" import in between — the import had to
be re-added once the usage existed. When splitting an addition across
multiple tool calls, expect the formatter to react to each one in isolation;
prefer making import + first-use changes in the same `Edit`/`Write` call, or
just double-check the file after if you don't.
