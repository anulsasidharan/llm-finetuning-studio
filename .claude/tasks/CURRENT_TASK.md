# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-004
## TASK NAME: POST /datasets/{id}/format + /quality-check endpoints
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-004-dataset-endpoints

## OBJECTIVE
Wire the two `training_engine` modules built in Week 3 (PHASE1-WEEK3-002's
`formatter.to_chatml`/`detect_format` and PHASE1-WEEK3-003's
`quality_check.run_quality_check`) into the FastAPI backend's dataset
routes per CLAUDE.md section 5:
- `POST /api/v1/datasets/{id}/format` — detect/normalize a dataset's rows
  to canonical ChatML, presumably persisting `Dataset.format`
  (currently always `"unknown"` per PHASE1-WEEK3-001's explicit deferral)
- `POST /api/v1/datasets/{id}/quality-check` — run `run_quality_check`
  over the dataset's (formatted) rows and persist the result into
  `Dataset.quality_report` (JSONB column, already on the ORM model)

## ACCEPTANCE CRITERIA (DRAFT — confirm against CLAUDE.md before starting)
- [ ] Confirm scope with the user first: **`apps/backend` cannot import
      `training_engine` directly today** — they're separate
      `requirements.txt`/`.venv` environments per the standalone-process
      architecture (CLAUDE.md's directory structure lists them as
      siblings, and nothing currently wires one to import the other).
      Decide the calling convention before writing code: e.g. (a) add
      `training_engine` as an installed dependency of `apps/backend`
      (blurs the "standalone process" boundary — confirm this is
      acceptable), (b) duplicate/port the needed logic into
      `apps/backend/services/`, or (c) dispatch via Celery task to a
      worker that *does* have `training_engine` installed (matches the
      "GPU compute process" framing in CLAUDE.md but may be overkill for
      a fast, synchronous quality-check call). This is a real
      architectural fork — do not guess silently.
- [ ] Read the dataset's actual row content back from MinIO storage
      (uploaded as raw bytes in PHASE1-WEEK3-001 — `services/dataset_service.py`
      stores the object but does not parse rows out of it past a row
      count) before formatting/quality-checking it
- [ ] `POST /datasets/{id}/format` — 200/201, persists detected/normalized
      format, returns the updated `DatasetResponse`
- [ ] `POST /datasets/{id}/quality-check` — 200, persists
      `Dataset.quality_report`, returns the report (or updated
      `DatasetResponse` with it embedded — confirm shape)
- [ ] Both routes behind `Depends(get_current_user)`, scoped to the
      current user's own datasets (404 if not found/not owned — follow
      the existing `test_dataset_routes.py` pattern)
- [ ] Tests in `apps/backend/tests/test_dataset_routes.py` (extend
      existing file) — mock the MinIO read exactly like PHASE1-WEEK3-001
      did for the upload (no live MinIO in CI, see ARCHITECTURE DECISIONS)
- [ ] `uv run pytest -q` passes in `apps/backend`
- [ ] `uv run ruff check .` and `uv run ruff format --check` pass in
      `apps/backend` on touched files

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-004-dataset-endpoints
```

### Step 2 — Confirm scope with the user before writing code
Resolve the cross-process calling-convention question above (this is
the main open design decision, bigger than prior Week 3 tasks' scope
questions — flag it clearly).

### Step 3 — Implement routes + service logic + tests

### Step 4 — Verify
```
(cd apps/backend && uv run pytest -q)
(cd apps/backend && uv run ruff check .)
(cd apps/backend && uv run ruff format --check api/ services/ tests/)
```
(Standing rule: always wrap `cd`-then-run sequences in a subshell
`(cd dir && cmd)` — applies to ANY directory navigation in the Bash tool.)

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK3-004
3. BACKLOG.md → PHASE1-WEEK3-004 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK3-005 (fine-tune job creation
   endpoint + config validation)

## BLOCKERS
The `apps/backend` ↔ `training_engine` calling-convention decision (see
acceptance criteria Step/criterion 1) must be resolved before
implementation starts — this is a genuine architectural fork, not a
pragmatic-default situation like prior Week 3 tasks' open questions.

## NOTES FOR NEXT TASK
Still open from PHASE1-WEEK2-009 (optional, low priority): `core/auth.py`'s
local `CREDENTIALS_EXCEPTION = HTTPException(401)` could be migrated to
the `core/exceptions.py` `UnauthorizedError` hierarchy now that both the
hierarchy and its FastAPI exception handler exist — not a hard
requirement, just consistency cleanup.

Known unrelated issue (not in scope, just flagged): `fts_backend`'s
Docker `start.sh` fails with `set: Illegal option -` on container start
in this environment — looks like a CRLF line-ending issue from a Windows
checkout corrupting a `set -euo pipefail` (or similar) line. Verification
has been worked around by running the app locally via `uv run uvicorn`
against host-mapped ports instead of inside the `fts_backend` container.
Worth a dedicated fix-it task at some point.

**Testing rule, reconfirmed in PHASE1-WEEK3-001:** CI's `backend-test` job
(`.github/workflows/ci.yml`) only spins up Postgres + Redis service
containers — there is no MinIO service in CI. Any test that exercises a
code path touching `core/storage.py` MUST mock the storage call (e.g.
`monkeypatch.setattr(dataset_service, "upload_file", fake_fn)`), never hit
a real MinIO endpoint, or CI will fail with connection errors. DB-touching
tests are fine hitting the real Postgres (CI provides it) following the
existing `client` fixture / `psycopg2` cleanup pattern.

**Gotcha, repeated across multiple sessions:** the PostToolUse lint/format
hook auto-fixes "unused" imports between separate `Edit` calls — adding an
import in one `Edit` and its only usage in a later, separate `Edit` lets
the hook strip the import in between. Always add an import and its first
usage in the same `Edit`/`Write` call.

**Gotcha from PHASE1-WEEK3-002, still standing:** `training_engine/__init__.py`
was deleted because its mere presence broke `uv run pytest tests/` there —
pytest's rootdir package-walk treated `training_engine` as a subpackage
and walked one level too far up to the monorepo root for `sys.path`
insertion, causing local-package imports (`from datasets.formatter import
...`) to resolve against a same-named pip package instead. Do not
recreate `training_engine/__init__.py` without also adding explicit
`pythonpath` config for pytest. **This is directly relevant to this task**
if the chosen calling convention involves `apps/backend` importing
`training_engine` as a package — the import-resolution mechanics differ
between a real installed package and the current bare-directory layout.

**LANDMINE, still unresolved (not relevant to this task unless it touches
`loader.py`):** `training_engine/datasets/` collides by name with the
pip-installed `datasets==2.19.0` (HuggingFace) library in
`training_engine/requirements.txt`. Confirmed in PHASE1-WEEK3-003 that
neither `formatter.py` nor `quality_check.py` needs `import datasets`, so
it still hasn't triggered. Resolve before any future `loader.py` work.

**New dependency note from PHASE1-WEEK3-003:** `training_engine/datasets/quality_check.py`
uses `langdetect==1.0.9` with `DetectorFactory.seed = 0` set at import
time for deterministic results. If this task's calling convention pulls
`run_quality_check` into `apps/backend`'s process somehow, `langdetect`
would need to be added to `apps/backend/requirements.txt` too (it
currently only exists in `training_engine/requirements.txt`).

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-003)
Completed 2026-06-18. Built `training_engine/datasets/quality_check.py`:
`run_quality_check(rows: list[dict]) -> dict` over canonical ChatML rows
— exact-match dedup (normalized text key), word-count stats (min/max/
mean/median via `.split()`), and language detection via `langdetect`
(new dependency, seeded for determinism). Made and documented three
scope decisions from the draft acceptance criteria (exact dedup only, no
tokenizer, langdetect) rather than pausing on them. Confirmed the
`quality_check.py` module doesn't trigger the `training_engine/datasets/`
↔ pip `datasets` naming collision flagged in PHASE1-WEEK3-002, since it
never imports the HF library. 10 new tests in
`training_engine/tests/test_quality_check.py`. Full suite 27/27 passing,
ruff clean. Pushed `feat/PHASE1-WEEK3-003-quality-check`; PR not opened
(manual creation per established workflow).
