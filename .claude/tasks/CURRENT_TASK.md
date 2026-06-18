# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-009
## TASK NAME: core/exceptions.py — custom exception hierarchy
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-009-exceptions

## OBJECTIVE
Create `apps/backend/core/exceptions.py` defining the custom exception
hierarchy referenced by CLAUDE.md section 6 ("Exceptions: Custom hierarchy in
`core/exceptions.py`"). Depends only on `core/config.py` (PHASE1-WEEK2-001,
done) — no DB/auth/storage imports needed.

## ACCEPTANCE CRITERIA
- [ ] Base `AppException(Exception)` carrying at minimum `status_code: int`
      and `detail: str`, both set via `__init__` (don't subclass
      `HTTPException` directly — keep this hierarchy framework-agnostic so
      it can be raised from `core/`, `services/`, or `training_engine/`
      without a FastAPI import; routes/middleware translate `AppException`
      → `HTTPException` at the API boundary)
- [ ] Concrete subclasses covering the cases this codebase already needs:
      `NotFoundError` (404), `UnauthorizedError` (401), `ForbiddenError`
      (403), `ConflictError` (409), `ValidationError` (422) — each with a
      sensible default `detail` message that can be overridden
- [ ] Full type hints on `__init__` signatures
- [ ] No `print()` calls
- [ ] Unit test under `apps/backend/tests/test_exceptions.py` — assert each
      subclass's default `status_code`, that `detail` can be overridden via
      constructor arg, and that all subclasses are instances of
      `AppException`
- [ ] `uv run pytest -q` passes (existing 18 tests + new exceptions tests)
- [ ] `uv run ruff check .` and `uv run ruff format --check core/ tests/`
      pass on the files you touch (note: several other `core/`/`tests/`
      files have pre-existing format drift unrelated to this task — see
      SESSION LOG entries 2026-06-18 — don't let that block; just keep your
      new/edited files clean)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-009-exceptions
```

### Step 2 — Write core/exceptions.py
- `AppException` base class + the five concrete subclasses listed above
- Keep it dependency-free (stdlib only) so it can be imported anywhere in
  the codebase without pulling in FastAPI

### Step 3 — Write tests/test_exceptions.py
Config-only assertions per subclass (status_code default, detail override,
isinstance check) — no FastAPI app/client needed.

### Step 4 — Verify
```
(cd apps/backend && uv run pytest -q)
(cd apps/backend && uv run ruff check .)
(cd apps/backend && uv run ruff format --check core/ tests/)
```
(Remember: wrap `cd`-then-run sequences in a subshell so the outer shell's
cwd stays at repo root — otherwise the `.claude/hooks/lint.py` PostToolUse
hook breaks on the next Edit/Write. This has bitten almost every session in
Week 2 — always parenthesize `(cd dir && cmd)`.)

### Step 5 — Stage, commit, push
```
git add apps/backend/core/exceptions.py apps/backend/tests/test_exceptions.py
git commit -m "feat(exceptions): PHASE1-WEEK2-009 custom exception hierarchy"
git push origin feat/PHASE1-WEEK2-009-exceptions
```

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-009
3. BACKLOG.md → PHASE1-WEEK2-009 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-010 content (main.py FastAPI
   app factory)

## FILES TO UPDATE IN THIS TASK
- apps/backend/core/exceptions.py
- apps/backend/tests/test_exceptions.py

## BLOCKERS
None.

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-010 (`main.py` FastAPI app factory + router
registration + CORS) depends on `core/auth.py` (done). Once
PHASE1-WEEK2-009 lands, consider (in a later task, not as a surprise inside
this one) whether `core/auth.py`'s local `CREDENTIALS_EXCEPTION =
HTTPException(401)` should be migrated to the new `UnauthorizedError`
hierarchy — don't do that refactor here unless asked.
After main.py: health endpoint (PHASE1-WEEK2-011), then auth routes
(PHASE1-WEEK2-012), then seed_data (PHASE1-WEEK2-013) — continue down the
Week 2 backlog in dependency order.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK2-008)
Completed 2026-06-18. Created `core/celery_app.py` — module-level
`celery = Celery("fts", broker=settings.CELERY_BROKER_URL,
backend=settings.CELERY_RESULT_BACKEND)` (confirmed against installed
`celery==5.4.0`), with `celery.conf.update(...)` setting
`task_serializer`/`result_serializer="json"`, `accept_content=["json"]`,
`timezone="UTC"`, `enable_utc=True`, `task_routes` mapping
`"tasks.training_tasks.*"` → `{"queue": "training"}` and
`"tasks.export_tasks.*"` → `{"queue": "export"}`, and
`task_default_queue="default"` — matching the `--queues=training,export,
default` flag already in `docker-compose.yml`'s `celery_worker` command.
Added 4 config-only unit tests in `tests/test_celery_app.py` (app name,
broker/backend resolve from settings, serialization defaults, task_routes
mapping) — full suite now 18/18 passing. `ruff check .` clean; `ruff format
--check` clean on both new files.

**Real bug found + fixed while verifying containers (required by this
task's acceptance criteria):** `core/config.py`'s
`REPO_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"` raised
`IndexError` inside the `celery_worker`/`celery_beat` containers, because
`core/config.py` lives at `/app/core/config.py` there (only 2 parent levels
above `/`) vs `apps/backend/core/config.py` locally (4 levels to repo
root) — this was the actual cause of those containers restart-looping, not
the missing `celery_app.py` module alone. Fixed by guarding the lookup:
```python
_CONFIG_PARENTS = Path(__file__).resolve().parents
REPO_ROOT_ENV_FILE = _CONFIG_PARENTS[3] / ".env" if len(_CONFIG_PARENTS) > 3 else None
```
Safe because the containers already receive every required var via
docker-compose's `env_file: .env` directive (injected straight into the
container environment) — the `.env` *file* lookup inside the container is
redundant, it just needs to not crash. Verified locally (`uv run pytest -q`
still 18/18 after the fix) and in Docker (`docker compose restart
celery_worker celery_beat` → both `Up`, not `Restarting`, after 15s+;
`celery_worker` log shows clean `Connected to redis://...` + `ready`).
Also added `celerybeat-schedule` (celery beat's runtime sqlite artifact,
written to `apps/backend/` on startup) to root `.gitignore`. Committed as
two commits on the branch: the celery_app feature commit, then a separate
`fix(config): ...` commit for the config.py guard. Pushed
`feat/PHASE1-WEEK2-008-celery-app`; PR not opened (manual creation per
established workflow).

**Gotcha repeated again:** running `uv run python -c "import celery; ..."`
as a bare `cd apps/backend && ...` (Bash tool, no subshell parens) leaked
the cwd forward exactly as documented in PHASE1-WEEK2-004/005/007 — caught
it immediately via `pwd` before the next file write and recovered with a
plain `cd` back to repo root. This is now the fourth time — treat
`(cd dir && cmd)` as completely non-negotiable, including for one-line
version checks.
