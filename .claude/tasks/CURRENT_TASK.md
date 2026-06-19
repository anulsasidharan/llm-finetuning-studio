# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-002
## TASK NAME: training_engine/datasets/formatter.py — Alpaca/ShareGPT/ChatML
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-002-dataset-formatter

## OBJECTIVE
Per CLAUDE.md section 2 (training_engine/datasets/) and section 9
(DATASET FORMATS): build `training_engine/datasets/formatter.py` that can
detect and normalize the three supported dataset formats — Alpaca,
ShareGPT, ChatML — from raw uploaded dataset rows (the rows produced by
PHASE1-WEEK3-001's upload endpoint, currently stored with
`Dataset.format = "unknown"`). This is a `training_engine` module, not a
FastAPI route — the route wiring (`POST /datasets/{id}/format`) is a
separate, later task (PHASE1-WEEK3-004).

## ACCEPTANCE CRITERIA (DRAFT — confirm against CLAUDE.md before starting)
- [ ] `training_engine/datasets/formatter.py` — format detector + per-format
      normalizer functions, e.g. `detect_format(row: dict) -> str` and
      `to_chatml(row: dict, format: str) -> dict` (or similar — confirm
      target shape with the user; CLAUDE.md doesn't specify a canonical
      internal representation yet)
- [ ] Recognizes the three shapes from CLAUDE.md section 9 exactly:
      - alpaca: `{"instruction", "input", "output"}`
      - sharegpt: `{"conversations": [{"from", "value"}, ...]}`
      - chatml: `{"messages": [{"role", "content"}, ...]}`
- [ ] Raises/handles unrecognized rows sensibly (confirm exact error
      handling approach with the user — likely a `core.exceptions` type,
      but `training_engine` doesn't currently depend on `apps/backend`'s
      `core/` package, so check whether that import is even allowed
      before assuming it)
- [ ] Unit tests in `training_engine/tests/` (confirm dir exists/pattern)
      covering: detection of each of the 3 formats, round-trip
      normalization, and at least one malformed-row case
- [ ] `uv run pytest -q` passes in `training_engine/`
- [ ] `uv run ruff check .` and `uv run ruff format --check` pass in
      `training_engine/` on touched files

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-002-dataset-formatter
```

### Step 2 — Confirm scope with the user before writing code
This task's acceptance criteria above is a DRAFT — `training_engine/`
has no existing code to pattern-match against yet (this is the first
task to touch it in Phase 1), so confirm: the exact function signatures,
the canonical internal row shape (probably ChatML-style `messages`, since
that's what `trl.SFTTrainer`/`DPOTrainer` generally expect, but confirm),
and whether `training_engine` should depend on anything in
`apps/backend/core/` (current architecture keeps them separate processes
— probably not, but confirm) before implementing.

### Step 3 — Implement formatter.py + tests

### Step 4 — Verify
```
(cd training_engine && uv run pytest -q)
(cd training_engine && uv run ruff check .)
(cd training_engine && uv run ruff format --check datasets/)
```
(Standing rule: always wrap `cd`-then-run sequences in a subshell
`(cd dir && cmd)` — applies to ANY directory navigation in the Bash tool.)

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK3-002
3. BACKLOG.md → PHASE1-WEEK3-002 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK3-003 (quality_check.py)

## BLOCKERS
None known.

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

**Gotcha, repeated again in PHASE1-WEEK3-001:** the PostToolUse lint/format
hook auto-fixes "unused" imports between separate `Edit` calls — adding an
import in one `Edit` and its only usage in a later, separate `Edit` lets
the hook strip the import in between. Always add an import and its first
usage in the same `Edit`/`Write` call.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-001)
Completed 2026-06-18. Built the dataset upload flow: `schemas/dataset.py`
(`DatasetResponse`), `services/dataset_service.py` (extension + content-type
+ size validation, MinIO upload via `core/storage.py`, row counting for
`.json`/`.jsonl`, creates `Dataset` row with `format="unknown"` since
format detection is this next task), and `api/v1/routes/datasets.py`
(`POST /datasets/upload`, `GET /datasets`, both JWT-protected), wired into
`api_router`. Fixed a real bug: was about to pass the already-exhausted
`file.file` stream to `upload_file` after `await file.read()` — switched to
`BytesIO(contents)`. Tests mock the MinIO call since CI has no MinIO
service container; DB assertions hit the real dev Postgres like
`test_auth_routes.py`. Full suite 55/55 passing, ruff clean on all
touched/new files. Pushed `feat/PHASE1-WEEK3-001-dataset-upload`; PR not
opened (manual creation per established workflow).
