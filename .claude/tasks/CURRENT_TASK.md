# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-008
## TASK NAME: training_engine/utils/gpu_monitor.py — pynvml metrics
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-008-gpu-monitor

## OBJECTIVE
Per CLAUDE.md section 2 (`training_engine/utils/`) and BACKLOG.md — build a
`pynvml`-based GPU monitor that reports live `gpu_utilization_pct` and
`vram_used_gb` (matching the `fine_tune_jobs` column names), so
`MetricsCallback` (PHASE2-007, now done) can be constructed with a real
`gpu_monitor` callable instead of always publishing `None` for those two
fields.

## CONTEXT FROM PHASE2-007
- `training_engine/utils/callbacks.py`'s `MetricsCallback.__init__` already
  accepts an optional `gpu_monitor: Callable[[], dict[str, Any]] | None`
  kwarg — calling it (no args) once per `on_log`/`on_evaluate` publish and
  merging `gpu_utilization_pct`/`vram_used_gb` from its returned dict into
  the payload. **This task's deliverable should be a zero-arg callable (or a
  class exposing one, e.g. `GPUMonitor().sample`) with exactly those two
  keys** so it can be passed straight into `MetricsCallback(gpu_monitor=...)`
  with no adapter glue.
- `pynvml==11.5.0` is already pinned in `training_engine/requirements.txt`
  (added in some earlier session, unused until now — confirmed via
  `requirements.txt` read during PHASE2-007).
- No GPU is guaranteed to be present in dev/CI — `pynvml.nvmlInit()` raises
  `NVMLError_LibraryNotFound` (or similar) on a machine with no NVIDIA driver.
  The monitor must degrade gracefully (return `None`/omit the two keys, not
  raise) when pynvml can't initialize — `MetricsCallback`'s `_gpu_stats()`
  already does `gpu_stats.get(...)`, tolerant of a partial or empty dict.
  Mirror the lazy-import-for-testability pattern used everywhere else in
  `training_engine` (e.g. `_get_bitsandbytes_config_cls()` in
  `qlora_trainer.py`, `_get_trl_orpo_trainer()` in `orpo_trainer.py`) so unit
  tests can mock pynvml entirely — never call real NVML in CI/unit tests.
- `vram_used_gb` should read whichever GPU index the trainer is actually
  running on (`torch.cuda.current_device()` if CUDA is active, via
  `BaseTrainer.resolve_device()`'s same pattern) — decide whether
  `GPUMonitor` takes a device index at construction or always reports
  device 0; single-GPU dev/training is the only case that matters today
  (CLAUDE.md's GPU vendor list doesn't yet describe multi-GPU jobs).

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] `training_engine/utils/gpu_monitor.py` — a callable/class returning
      `{"gpu_utilization_pct": float, "vram_used_gb": float}` (or `{}`/partial
      when unavailable)
- [ ] Returns gracefully (no raise) when no NVIDIA GPU / pynvml init fails
- [ ] Unit tests mock `pynvml` entirely — no real NVML/GPU call in tests
- [ ] `uv run ruff check .` and `uv run pytest tests/` clean in
      `training_engine/`
- [ ] Wire a real `GPUMonitor` instance into at least one example of
      `MetricsCallback(gpu_monitor=...)` construction (decide where — likely
      stays the Celery training task's job once PHASE2-009 lands; flag if
      this task should leave that wiring for PHASE2-009 instead of forcing it
      in now)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-008-gpu-monitor
```

### Step 2 — Implement gpu_monitor.py + tests

### Step 3 — Verify
`(cd training_engine && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/)`

### Step 4 — Stage, commit, push

### Step 5 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-007)
Completed 2026-06-21. Built `training_engine/utils/callbacks.py` —
`MetricsCallback(TrainerCallback)` hooking `on_log`/`on_evaluate` (not
`on_step_end`, to avoid flooding Redis every single step) and publishing a
`{"type": "metrics_update", "job_id", "step", "epoch", "train_loss",
"eval_loss", "gpu_utilization_pct", "vram_used_gb", "tokens_per_second"}`
payload to Redis pub/sub channel `training_metrics:{job_id}` — this exact
channel name and payload-type convention turned out to already be documented
in MEMORY.md's pre-existing "WEBSOCKET PATTERN" section (written ahead of
this task), so no new naming decision was actually needed, just implementing
to the existing contract. Resolved the "wire into BaseTrainer by default vs.
caller-injected" open question from CURRENT_TASK.md's draft: kept
`BaseTrainer.get_callbacks()` caller-injected (unchanged behavior, preserves
the existing `test_get_callbacks_returns_copy` assertion) — the future Celery
training task constructs `MetricsCallback(job_id=...)` itself and passes it
via the existing `callbacks=` kwarg, consistent with how `dataset_rows` and
every other external dependency is already threaded into trainers. Redis
client config reads `TRAINING_ENGINE_REDIS_URL` (already declared in
`.env.example`, db index 3, separate from the backend's db 0), falling back
to `redis://localhost:6380/3` for local-outside-Docker runs. `redis==5.0.4`
was already pinned in `training_engine/requirements.txt` (no new dependency
needed) — imported at module level (not lazily, unlike trl/peft/bitsandbytes)
since it's a lightweight, already-required dependency with no GPU/native
stack to dodge in tests. Took an optional `gpu_monitor` callable + optional
injected `redis_client` (both for testability and to leave PHASE2-008's
pynvml monitor as a clean drop-in). Publish failures are caught and logged
via `structlog.warning`, not raised — a transient Redis hiccup shouldn't
crash a long-running training job. 14 new tests in `test_callbacks.py`
(channel naming, custom channel override, env var default/fallback, on_log
publishes train_loss, ignores logs without loss/eval_loss, ignores
empty/None logs, on_evaluate publishes eval_loss, ignores metrics without
eval_loss, gpu_monitor stats included/omitted, publish failure swallowed,
lazy redis client built from url, injected client reused) — full suite
73/73 passing. Hit the standing "PostToolUse hook strips a freshly-added
unused import between separate Edit calls" gotcha once (added `import redis`
in one edit with its usage already in the file from an earlier edit — this
time it survived since usage was already present); also hit the standing
"bare `cd dir && cmd` leaks Bash cwd forward" gotcha once during verification
(an earlier `cd training_engine && ...` without subshell parens leaked cwd,
breaking a later `git add training_engine/...` with "No such file or
directory" since it was now relative to an already-training_engine cwd) —
recovered with `cd /e/.../Unified_Finetuning_studio` back to repo root.
`uv run ruff check .` clean; `uv run ruff format --check .` flagged the same
~20 pre-existing CRLF-drift files noted across every prior training_engine
session — confirmed via the file list that neither `callbacks.py` nor
`test_callbacks.py` are among them. Pre-commit hook (ruff lint + format on
training_engine) passed automatically. Pushed `feat/PHASE2-007-metrics-
callbacks`.
