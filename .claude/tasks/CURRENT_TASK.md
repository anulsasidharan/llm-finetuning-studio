# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-009
## TASK NAME: Celery training task — dispatch to training engine
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-009-celery-training-task (not yet cut)

## OBJECTIVE
Per BACKLOG.md — build the Celery task (queue: `training`, per
`core/celery_app.py`'s `task_routes`) that takes a `FineTuneJob.id`, loads the
dataset rows from MinIO, picks and constructs the right `training_engine`
trainer for the job's `methodology`, wires `MetricsCallback` (PHASE2-007) +
`GPUMonitor` (PHASE2-008) into it, runs `train()`, and updates the job's
status/metrics columns in Postgres as it goes. This is the task that finally
makes `POST /jobs` (PHASE1-WEEK3-005) do something — today a created job just
sits at `status="pending"` forever.

## CONTEXT FROM PRIOR SESSIONS
- `apps/backend/tasks/__init__.py` exists but is empty — no task modules
  exist yet. CLAUDE.md section 2 names the target file
  `apps/backend/tasks/training_tasks.py`.
- `core/celery_app.py` already routes `tasks.training_tasks.*` → the
  `training` queue (PHASE1-WEEK2-008) — no celery config changes needed.
- **Process boundary problem to resolve first:** `training_engine`'s
  trainers (`BaseTrainer` + subclasses) live in a separate
  standalone-process/environment from `apps/backend` (see ARCHITECTURE
  DECISIONS — this is the same boundary PHASE1-WEEK3-004 hit, resolved there
  by *porting* dataset-format/quality-check logic into
  `apps/backend/services/`). Training is not a quick synchronous port
  candidate (real GPU compute, heavy ML deps, long-running) — needs a real
  decision on how the Celery worker process actually gets `training_engine`
  importable: e.g. install `training_engine` as a path/editable dependency
  into the backend's environment, run Celery workers from a working
  directory that has both on `sys.path`, or restructure `training_engine` as
  an installable package. **Confirm this with the user before writing code —
  it changes `docker-compose.gpu.yml`'s celery_worker service and possibly
  `apps/backend/requirements.txt`.**
- Trainer dispatch: map `FineTuneJob.methodology` → trainer class
  (`SFTTrainer`/`LoRATrainer`/`QLoRATrainer`/`DPOTrainer`/`ORPOTrainer`,
  `rlhf` has no trainer yet — PHASE4-005 stretch goal, so the task should
  reject/skip `rlhf` jobs for now rather than crash).
- Dataset loading: `FineTuneJob.dataset_id` → `core.storage.download_file` →
  parse rows (reuse `services/dataset_service._parse_rows` or the same
  pattern) → pass as `dataset_rows` to the trainer constructor. DPO/ORPO need
  preference-pair rows (`{"prompt","chosen","rejected"}`), not ChatML — the
  job's dataset must already be in that shape for those two methodologies;
  decide whether to validate this before dispatch or let the trainer's own
  `prepare_preference_rows()` raise `TrainerError`.
- Status/metrics updates: `FineTuneJob` has `status`, plus live metric
  columns (`train_loss`, `eval_loss`, `gpu_utilization_pct`, `vram_used_gb`,
  `tokens_per_second` — see CLAUDE.md section 4). Decide whether this task
  also needs to *subscribe* to its own `MetricsCallback` Redis publishes to
  persist periodic snapshots into Postgres, or whether DB updates are just
  coarse-grained (`pending → running → completed/failed`) and per-step
  metrics live only in Redis/the eventual WebSocket hub (PHASE2-010) without
  ever landing in Postgres. **Flag this as a real open question — CLAUDE.md
  doesn't say, and it affects whether `experiments`/`registry` pages later
  read live metrics from the DB or only from the WebSocket stream.**
- Construct `MetricsCallback(job_id=job.id, gpu_monitor=GPUMonitor().sample)`
  per this session's PHASE2-008 work — both classes already accept exactly
  the kwargs needed, no adapter glue required (see
  `training_engine/tests/test_gpu_monitor.py::test_wires_into_metrics_callback_gpu_monitor_kwarg`
  for a concrete usage example to mirror).
- Async/sync mismatch: Celery tasks are sync; `apps/backend`'s DB layer is
  async-only (`core/database.py`, `AsyncSessionLocal`). Needs a deliberate
  decision on how this task touches Postgres from inside a sync Celery
  task — e.g. a sync engine/session via `DATABASE_URL_SYNC` (already exists,
  used by Alembic/scripts) rather than forcing `asyncio.run()` inside Celery.

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] `apps/backend/tasks/training_tasks.py` — a Celery task taking a job ID,
      dispatching to the right `training_engine` trainer, updating job
      status (`running` → `completed`/`failed`) in Postgres
- [ ] `training_engine` is actually importable from the Celery worker
      process — real fix, not just "works on this dev machine"
- [ ] `MetricsCallback` + `GPUMonitor` wired into the trainer's `callbacks=`
- [ ] `rlhf` methodology jobs fail clearly (no trainer exists yet), not crash
      unhandled
- [ ] Unit tests mock the trainer classes / Celery's sync execution — no real
      GPU/model download in tests
- [ ] `ruff check`/`ruff format --check` clean in `apps/backend`

## STEPS TO COMPLETE

### Step 1 — Confirm the process-boundary + DB-access design questions above
with the user before writing code (genuine forks, not guessable from
existing code/CLAUDE.md).

### Step 2 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-009-celery-training-task
```

### Step 3 — Implement training_tasks.py + tests

### Step 4 — Verify
`(cd apps/backend && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/)`

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-008)
Completed 2026-06-21. Built `training_engine/utils/gpu_monitor.py` —
`GPUMonitor` class (constructor takes `device_index: int = 0`, default 0 for
the single-GPU dev/training case) with a `sample()` method (and `__call__`
alias) returning `{"gpu_utilization_pct": float, "vram_used_gb": float}` via
lazily-imported `pynvml` (`_get_pynvml()` helper, mirrors the
`_get_bitsandbytes_config_cls()`/`_get_trl_orpo_trainer()` lazy-import
pattern used elsewhere in `training_engine` for testability). Degrades to
`{}` on any failure (`nvmlInit` raising when no NVIDIA driver is present,
handle/utilization/memory lookups failing) — every failure path is caught
and logged via `structlog.warning`, never raised, since this is sampled
inside `MetricsCallback` on every `on_log`/`on_evaluate` of a real,
expensive, long-running training run. `nvmlShutdown()` runs in a `finally`
that itself swallows failures, so a broken shutdown never masks/crashes the
caller. `pynvml==11.5.0` was already pinned in `training_engine/requirements.txt`
(unused until now) — no new dependency. 9 new tests in
`test_gpu_monitor.py` (success path returns correct keys, device_index
passed to handle lookup, `nvmlInit` failure → `{}`, handle-lookup failure →
`{}`, shutdown still called on a mid-sample failure, shutdown failure itself
swallowed, `__call__` delegates to `sample()`, default device_index is 0,
and one integration-style test constructing a real
`MetricsCallback(gpu_monitor=GPUMonitor(device_index=0).sample)` with mocked
pynvml end-to-end through `on_log` to prove the zero-adapter-glue contract
from PHASE2-007 holds) — full suite 82/82 passing. `uv run ruff check .`
clean; `uv run ruff format --check .` flagged the same pre-existing
CRLF-drift files noted every prior training_engine session (confirmed via
`git status` that neither new file is among them). Hit the standing
"PostToolUse hook strips a freshly-added unused import between separate Edit
calls" gotcha twice in a row on the same file (added `json`/`MetricsCallback`
imports before their usage existed in two separate edits) — recovered by
re-adding both imports in a single `Edit` once usage was already present in
the file. Also hit the standing "bare `cd dir && cmd` leaks Bash cwd
forward" gotcha once (a `cd training_engine && uv run ruff check .` without
subshell parens), which broke the next Edit's PostToolUse lint hook
(`.claude/hooks/lint.py` not found relative to the leaked cwd) — recovered
with a plain `cd` back to repo root; reinforces the standing
`(cd dir && cmd)` subshell rule still needs to be followed every time, even
mid-verification. Pushed `feat/PHASE2-008-gpu-monitor`; PR not opened
(manual creation per established workflow).
