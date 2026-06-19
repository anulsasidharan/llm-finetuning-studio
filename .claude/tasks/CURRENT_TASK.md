# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-005
## TASK NAME: Fine-tune job creation endpoint + config validation
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-005-job-creation

## OBJECTIVE
Per CLAUDE.md section 5 / Week 3 checklist: build the `FineTuneJob`
creation flow — `POST /api/v1/jobs` validates the submitted training
config against the chosen methodology (SFT/LoRA/QLoRA/DPO/ORPO/RLHF, see
CLAUDE.md section 7) before persisting the job row, plus the supporting
read routes (`GET /jobs`, `GET /jobs/{job_id}`, `GET /jobs/{job_id}/config`)
needed for the frontend Config Builder work later in Week 3.

## ACCEPTANCE CRITERIA (DRAFT — confirm against CLAUDE.md before starting)
- [ ] `schemas/job.py` — request schema for job creation (base_model_id,
      methodology, training_config dict, optional dataset_id, gpu_type,
      cloud_vendor) and a `FineTuneJobResponse`
- [ ] Config validation: methodology must be one of the six supported
      values; `training_config` must satisfy whatever minimum shape that
      methodology needs (confirm exact required keys per methodology with
      the user before coding — CLAUDE.md section 7 gives VRAM/min-samples
      guidance, not a strict config schema, so this is a real scope
      decision, not a pragmatic default)
- [ ] If `dataset_id` is provided, confirm it exists and belongs to the
      current user (404 otherwise) — reuse `dataset_service.get_dataset`
      pattern from PHASE1-WEEK3-004
- [ ] `POST /api/v1/jobs` — creates a `FineTuneJob` row with `status` set
      to its initial pending state; 422 on invalid config/methodology
- [ ] `GET /api/v1/jobs` — current user's jobs only
- [ ] `GET /api/v1/jobs/{job_id}` — 404 if not found/not owned
- [ ] `GET /api/v1/jobs/{job_id}/config` — returns just the
      `training_config` JSONB
- [ ] All routes behind `Depends(get_current_user)`
- [ ] Tests in a new `apps/backend/tests/test_job_routes.py`
- [ ] `uv run pytest -q` passes in `apps/backend`
- [ ] `uv run ruff check .` and `uv run ruff format --check` pass in
      `apps/backend` on touched files

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-005-job-creation
```

### Step 2 — Confirm scope with the user before writing code
Resolve the training-config validation shape (the main open design
question above) before implementation.

### Step 3 — Implement schema + service logic + routes + tests

### Step 4 — Verify
```
(cd apps/backend && uv run pytest -q)
(cd apps/backend && uv run ruff check .)
(cd apps/backend && uv run ruff format --check api/ schemas/ services/ tests/)
```
(Standing rule: always wrap `cd`-then-run sequences in a subshell
`(cd dir && cmd)` — applies to ANY directory navigation in the Bash tool.)

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK3-005
3. BACKLOG.md → PHASE1-WEEK3-005 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with next Week 3 task (PHASE1-WEEK3-006:
   frontend Next.js root layout + sidebar + header)

## BLOCKERS
None yet identified — the training-config validation shape (acceptance
criteria above) needs confirming with the user before coding starts, but
unlike PHASE1-WEEK3-004's calling-convention fork this is expected to be
a quick scope confirmation, not a multi-option architectural decision.

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

**Testing rule, reconfirmed through PHASE1-WEEK3-004:** CI's
`backend-test` job (`.github/workflows/ci.yml`) only spins up Postgres +
Redis service containers — there is no MinIO service in CI. Any test that
exercises a code path touching `core/storage.py` MUST mock the storage
call (e.g. `monkeypatch.setattr(dataset_service, "upload_file"/"download_file", fake_fn)`),
never hit a real MinIO endpoint, or CI will fail with connection errors.
DB-touching tests are fine hitting the real Postgres (CI provides it)
following the existing `client` fixture / `psycopg2` cleanup pattern.

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
`pythonpath` config for pytest.

**LANDMINE, still unresolved (not relevant unless a future task touches
`training_engine/datasets/loader.py`):** `training_engine/datasets/`
collides by name with the pip-installed `datasets==2.19.0` (HuggingFace)
library in `training_engine/requirements.txt`. Confirmed in
PHASE1-WEEK3-003/004 that neither `formatter.py`, `quality_check.py`, nor
their `apps/backend/services/` ports need `import datasets`, so it still
hasn't triggered. Resolve before any future `loader.py` work.

**New architectural pattern from PHASE1-WEEK3-004:** when a route needs
logic that lives in `training_engine` (a separate standalone
process/environment from `apps/backend`, per CLAUDE.md), the established
answer is to **port** that logic into `apps/backend/services/` as a
near-verbatim copy, rather than installing `training_engine` as a backend
dependency or dispatching via Celery — confirmed with the user as the
right tradeoff for fast, synchronous, CPU-only operations. This means
`services/dataset_format.py`/`services/dataset_quality.py` and
`training_engine/datasets/formatter.py`/`quality_check.py` are two
independent copies of the same logic and must be kept in sync by hand if
either evolves. Apply the same pattern if a future task needs other
`training_engine` logic synchronously from the backend.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-004)
Completed 2026-06-18. Confirmed with the user to port (not import/Celery-
dispatch) `training_engine`'s formatter + quality_check logic into
`apps/backend/services/dataset_format.py` / `dataset_quality.py`. Added
`get_dataset`/`format_dataset`/`quality_check_dataset` to
`services/dataset_service.py`; wired `POST /datasets/{id}/format` and
`POST /datasets/{id}/quality-check` (both `Depends(get_current_user)`,
404 if not found/not owned, returns updated `DatasetResponse`). Added
`langdetect==1.0.9` to `apps/backend/requirements.txt`. 13 new tests in
`tests/test_dataset_routes.py` (new `mock_minio_download` fixture, no
live MinIO). Full suite 64/64 passing, ruff clean. Pushed
`feat/PHASE1-WEEK3-004-dataset-endpoints`; PR not opened (manual creation
per established workflow).
