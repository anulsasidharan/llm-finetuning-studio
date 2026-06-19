# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-003
## TASK NAME: training_engine/datasets/quality_check.py — dedup, stats, language
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-003-quality-check

## OBJECTIVE
Per CLAUDE.md section 2 (training_engine/datasets/) and the Week 3
checklist ("Dataset format + quality check services"): build
`training_engine/datasets/quality_check.py` that runs basic quality
checks over a normalized dataset (the canonical `{"messages": [...]}`
rows produced by PHASE1-WEEK3-002's `to_chatml()`) — deduplication,
summary statistics, and language detection — and returns a quality
report. This is a `training_engine` module, not a FastAPI route — the
route wiring (`POST /datasets/{id}/quality-check`) is a separate, later
task (PHASE1-WEEK3-004). `Dataset.quality_report` (JSONB column, already
on the ORM model) is the eventual destination for this report's output.

## ACCEPTANCE CRITERIA (DRAFT — confirm against CLAUDE.md before starting)
- [ ] `training_engine/datasets/quality_check.py` — e.g. a
      `run_quality_check(rows: list[dict]) -> dict` entrypoint (confirm
      target shape with the user; no canonical quality-report schema
      exists yet)
- [ ] Deduplication: detect exact-duplicate rows (confirm: exact match
      on normalized content, or near-duplicate/fuzzy matching — fuzzy
      is a much bigger scope increase, confirm before assuming it)
- [ ] Summary stats: row count, duplicate count, token/word count
      distribution (confirm what's actually measurable without pulling
      in a tokenizer — `transformers`/`tiktoken` are heavy deps; word
      count via simple `.split()` may be the pragmatic v1)
- [ ] Language detection: confirm library choice — nothing in
      `training_engine/requirements.txt` currently provides this (no
      `langdetect`/`fasttext`/`langid`); decide whether to add a new
      dependency or defer/stub this part
- [ ] **IMPORTANT — read this before starting:** PHASE1-WEEK3-002 found
      that `training_engine/datasets/` (the local package) has the exact
      same import name as the pip-installed `datasets==2.19.0`
      (HuggingFace) library already in `requirements.txt`. If this task's
      implementation needs `import datasets` for anything (e.g. using HF
      `datasets` utilities for dedup/stats), that import will resolve to
      the local package instead, not the pip library. Resolve this
      naming collision (rename the local package, alias the import, or
      a different approach) before writing code that needs the real HF
      library — see MEMORY.md's "LANDMINE (unresolved)" entry.
- [ ] Unit tests in `training_engine/tests/test_quality_check.py`
      covering: duplicate detection, stats on a small known dataset, at
      least one language-detection case (or a documented stub/skip if
      language detection is deferred)
- [ ] `uv run pytest -q` passes in `training_engine/`
- [ ] `uv run ruff check .` and `uv run ruff format --check` pass in
      `training_engine/` on touched files

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-003-quality-check
```

### Step 2 — Confirm scope with the user before writing code
Resolve the `datasets` naming-collision landmine first (see above) if
this task needs the real HuggingFace library. Then confirm: exact
dedup strategy (exact vs fuzzy), what stats are in v1 scope, and the
language-detection library/dependency decision.

### Step 3 — Implement quality_check.py + tests

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
2. DONE.md → add row for PHASE1-WEEK3-003
3. BACKLOG.md → PHASE1-WEEK3-003 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK3-004 (dataset endpoints)

## BLOCKERS
None known, but see the `datasets` naming-collision landmine above —
may need to be resolved as part of this task's scope-confirmation step.

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

**New gotcha from PHASE1-WEEK3-002:** `training_engine/__init__.py` was
deleted because its mere presence broke `uv run pytest tests/` there —
pytest's rootdir package-walk treated `training_engine` as a subpackage
and walked one level too far up to the monorepo root for `sys.path`
insertion, causing local-package imports (`from datasets.formatter import
...`) to resolve against a same-named pip package instead. Do not
recreate `training_engine/__init__.py` without also adding explicit
`pythonpath` config for pytest.

**LANDMINE, unresolved, relevant to this task:** `training_engine/datasets/`
collides by name with the pip-installed `datasets==2.19.0` (HuggingFace)
library in `training_engine/requirements.txt`. `formatter.py` never needed
`import datasets` so it didn't surface, but `quality_check.py` might (e.g.
if comparing against any HF dataset utilities) — resolve this before
assuming a plain `import datasets` will reach the HF library. See
MEMORY.md ARCHITECTURE DECISIONS.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-002)
Completed 2026-06-18. Built `training_engine/datasets/formatter.py`:
`detect_format(row) -> str` (alpaca/sharegpt/chatml detection, raises
local `DatasetFormatError`) and `to_chatml(row, format=None) -> dict`
(normalizes any of the three to canonical `{"messages": [...]}`, the
shape `trl.SFTTrainer`/`DPOTrainer` expect). No dependency on
`apps/backend/core` — training_engine stays a standalone process. 17
new tests in `training_engine/tests/test_formatter.py`. Found and fixed
two real bugs during verification: `pytest` wasn't installed/declared
in `training_engine` at all (added `pytest==8.2.0` + new
`requirements-dev.txt`), and the empty/dead `training_engine/__init__.py`
broke pytest's import resolution by making it walk up to the monorepo
root instead of stopping at `training_engine` — deleted it. Surfaced
(but did not fix) a naming collision between the local
`training_engine/datasets/` package and the pip `datasets` (HuggingFace)
library — flagged for whichever future task needs `import datasets` for
real HF dataset loading. Full suite 17/17 passing, ruff clean. Pushed
`feat/PHASE1-WEEK3-002-dataset-formatter`; PR not opened (manual creation
per established workflow).
