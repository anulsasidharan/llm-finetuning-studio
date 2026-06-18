# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-008
## TASK NAME: core/celery_app.py — Celery app + queue routing
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-008-celery-app

## OBJECTIVE
Create `apps/backend/core/celery_app.py` defining the Celery application
instance that `celery_worker` and `celery_beat` (already wired in
`docker-compose.yml`) invoke as `celery -A core.celery_app worker
--queues=training,export,default` and `celery -A core.celery_app beat`
respectively. These two containers are currently restart-looping because
this module doesn't exist yet. Depends only on `core/config.py`
(PHASE1-WEEK2-001, done).

## ACCEPTANCE CRITERIA
- [ ] Module-level `celery = Celery("fts", broker=settings.CELERY_BROKER_URL,
      backend=settings.CELERY_RESULT_BACKEND)` (confirm exact kwarg names
      against the installed `celery` version before writing — check
      `uv run python -c "import celery; print(celery.__version__)"`)
- [ ] Three queues defined/routable: `training`, `export`, `default` (matches
      the `--queues=training,export,default` flag already in
      `docker-compose.yml`'s `celery_worker` command — don't change that flag,
      build the app to match it)
- [ ] `celery.conf.task_routes` (or equivalent) routes tasks under
      `apps/backend/tasks/training_tasks.py` → `training` queue and
      `apps/backend/tasks/export_tasks.py` → `export` queue (both task modules
      don't exist yet — PHASE1-WEEK3+ — so route by task name pattern, e.g.
      `"tasks.training_tasks.*"` / `"tasks.export_tasks.*"`, anticipating
      those modules; don't create the task modules themselves in this task)
- [ ] Sensible defaults: `task_serializer="json"`, `result_serializer="json"`,
      `accept_content=["json"]`, `timezone="UTC"`, `enable_utc=True`
- [ ] Full type hints where applicable (Celery's own API is largely untyped,
      so this mainly applies to any helper functions you add — don't force
      hints onto Celery config calls that don't take typed params)
- [ ] No `print()` calls
- [ ] Unit test under `apps/backend/tests/test_celery_app.py` — assert the
      `celery` app name, broker/backend URLs resolve from `settings`, and the
      task_routes mapping contains the training/export patterns (no live
      Redis/broker connection needed — these are all config assertions)
- [ ] `uv run pytest -q` passes (existing 14 tests + new celery_app tests)
- [ ] `uv run ruff check .` and `uv run ruff format --check core/ tests/` pass
      on the files you touch (note: `core/__init__.py`, `core/config.py`,
      `core/database.py`, `core/security.py`, `core/auth.py`,
      `tests/conftest.py`, `tests/test_health.py`, `tests/test_security.py`,
      `tests/test_auth.py` have pre-existing format drift unrelated to this
      task — see SESSION LOG 2026-06-18 PHASE1-WEEK2-006/007 — don't let that
      block; just keep your new/edited files clean)
- [ ] After merge, verify `celery_worker`/`celery_beat` containers stop
      restart-looping: `docker compose up -d celery_worker celery_beat` then
      `docker compose ps` shows both `Up`/healthy, not `Restarting`

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-008-celery-app
```

### Step 2 — Write core/celery_app.py
- Check installed `celery` version's exact `Celery()` constructor and
  `conf.task_routes` / `conf.update()` API before writing — don't guess
- Single `celery` instance built once at module import time from `settings`
- No task definitions here — just the app + routing config (tasks come in
  PHASE1-WEEK3+)

### Step 3 — Write tests/test_celery_app.py
Config-only assertions (app name, broker/backend, task_routes) — no real
broker connection required.

### Step 4 — Verify
```
(cd apps/backend && uv run pytest -q)
(cd apps/backend && uv run ruff check .)
(cd apps/backend && uv run ruff format --check core/ tests/)
```
Then, separately, confirm the previously-restarting containers recover:
```
docker compose up -d celery_worker celery_beat
docker compose ps
```
(Remember: wrap `cd`-then-run sequences in a subshell so the outer shell's cwd
stays at repo root — otherwise the `.claude/hooks/lint.py` PostToolUse hook
breaks on the next Edit. This bit PHASE1-WEEK2-007 again via a bare
`cd apps/backend && uv run python -c ...` signature-check command — always
parenthesize.)

### Step 5 — Stage, commit, push
```
git add apps/backend/core/celery_app.py apps/backend/tests/test_celery_app.py
git commit -m "feat(celery): PHASE1-WEEK2-008 Celery app + queue routing"
git push origin feat/PHASE1-WEEK2-008-celery-app
```

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-008
3. BACKLOG.md → PHASE1-WEEK2-008 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-009 content (core/exceptions.py)

## FILES TO UPDATE IN THIS TASK
- apps/backend/core/celery_app.py
- apps/backend/tests/test_celery_app.py

## BLOCKERS
None.

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-009 (`core/exceptions.py` — custom exception
hierarchy) only depends on PHASE1-WEEK2-001. Note that `core/auth.py`
(PHASE1-WEEK2-006) currently defines its own local `CREDENTIALS_EXCEPTION =
HTTPException(401)` because `core/exceptions.py` didn't exist yet — once
PHASE1-WEEK2-009 lands, consider (in that task or a follow-up) whether
`core/auth.py` should be updated to use the new hierarchy instead, but don't
do that refactor as a surprise inside PHASE1-WEEK2-009 itself unless asked.
After exceptions: PHASE1-WEEK2-010 (`main.py` FastAPI app factory, depends on
auth — already done), then health endpoint, then auth routes, then
seed_data — continue down the Week 2 backlog in dependency order.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-007)
Completed 2026-06-18. Created `core/storage.py` — module-level `minio_client
= Minio(f"{settings.MINIO_HOST}:{settings.MINIO_PORT}",
access_key=settings.MINIO_ROOT_USER, secret_key=settings.MINIO_ROOT_PASSWORD,
secure=settings.MINIO_USE_SSL)` built once at import time, plus thin wrapper
functions `upload_file`/`download_file`/`get_presigned_url`/`delete_file`
calling the underlying `minio` SDK (`put_object`/`get_object`/
`presigned_get_object`/`remove_object`) — verified exact method signatures
against the installed `minio==7.2.7` via `inspect.signature` before writing
any code. `get_presigned_url` converts `expires_seconds: int` to a
`timedelta` since `presigned_get_object` requires one. `download_file` reads
the `BaseHTTPResponse` stream fully then calls `.close()` + `.release_conn()`
in a `finally` block per minio-py docs. No bucket names hardcoded — callers
pass one of the four `Settings` bucket constants (`BUCKET_DATASETS`, etc.).
Added 4 unit tests in `tests/test_storage.py`, all mocking
`core.storage.minio_client` via `unittest.mock.patch` — full suite now 14/14
passing. `ruff check .` clean; `ruff format --check core/storage.py
tests/test_storage.py` clean (one line-length wrap needed and fixed on
`get_presigned_url`'s return statement). Pre-commit hook passed
automatically. Pushed `feat/PHASE1-WEEK2-007-core-storage`; PR not opened
(manual creation per established workflow).

**Gotcha repeated:** running the `minio` signature-inspection command as a
bare `cd apps/backend && uv run python -c "..."` (no subshell parens) leaked
the cwd forward and broke the next `Write` tool call's PostToolUse lint hook
(`lint.py` resolved relative to the leaked `apps/backend` cwd and wasn't
found there). Recovered by confirming the written file's content was correct
via `Read`, then running a plain `cd` back to the repo root before
continuing. This is the third time this exact pattern has bitten a session
(see PHASE1-WEEK2-004 and PHASE1-WEEK2-005 session log entries) — always
wrap `cd`-then-run sequences in `(cd dir && cmd)`, with no exceptions, even
for "just checking something quickly" one-off commands.
