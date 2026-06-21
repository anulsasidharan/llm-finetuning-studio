# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-007
## TASK NAME: training_engine/utils/callbacks.py — MetricsCallback → Redis pub/sub
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-007-metrics-callbacks

## OBJECTIVE
Per CLAUDE.md section 2 (`training_engine/utils/`) and the Phase 2 backlog —
build a HuggingFace `TrainerCallback` subclass that publishes live training
metrics (train_loss, eval_loss, GPU utilization, VRAM, tokens/sec, step/epoch
progress) to Redis pub/sub during training, so the planned WebSocket hub
(PHASE2-010) can relay them to the browser in real time. This is the callback
every existing trainer's `BaseTrainer.get_callbacks()` already has a stub
comment for ("MetricsCallback added in PHASE2-007").

## CONTEXT FROM PHASE2-006
- All five trainers built so far (SFT, LoRA, QLoRA, DPO, ORPO) call
  `self.get_callbacks()` and pass the result into their respective TRL/HF
  trainer's `callbacks=` kwarg — confirmed working end-to-end with mocks in
  every trainer's test suite. `BaseTrainer.get_callbacks()` currently just
  returns `list(self._callbacks)` (whatever was passed into the constructor)
  — this task adds the actual `MetricsCallback` class; wiring it into
  `BaseTrainer`'s constructor/`get_callbacks()` by default (vs. the Celery
  caller passing it in explicitly) is an open design question for this task.
- `training_engine/requirements.txt` does not yet have a Redis client pinned
  — check before adding (`redis` vs `redis[hiredis]`); mirror whatever
  `apps/backend` already uses for its own Redis connection if reusable.
- Redis runs on **localhost:6380** outside Docker (not the default 6379) per
  the PORT MAP in MEMORY.md, with password auth on the host-mapped port —
  `REDIS_URL="redis://:fts_redis_dev_2024@localhost:6380/0"` confirmed
  PHASE1-WEEK3-011. `training_engine` is a separate standalone process from
  `apps/backend` (per CLAUDE.md's architecture decision) — it will need its
  own Redis connection config, not import `apps/backend/core/config.py`.
- No pub/sub channel naming convention exists yet anywhere in the codebase —
  this task is the first to define one (e.g. `training:{job_id}:metrics`).
  Whatever channel name is chosen here is a contract the future WebSocket hub
  (PHASE2-010) must subscribe to with the exact same name — write it down
  clearly in code/docstring since there's no other source of truth yet.
- `fine_tune_jobs` DB columns already exist for live metrics per CLAUDE.md
  section 4: `train_loss`, `eval_loss`, `gpu_utilization_pct`, `vram_used_gb`,
  `tokens_per_second` — the payload shape this callback publishes should line
  up with these field names so a future consumer can write straight through
  without renaming.
- GPU/VRAM monitoring itself (pynvml) is a separate backlog item
  (PHASE2-008, `utils/gpu_monitor.py`) — not yet built. This task's callback
  can leave GPU fields as `None`/omitted until PHASE2-008 lands, or take an
  optional GPU-monitor dependency injected in — decide based on whether
  PHASE2-008 should land first (check with user if sequencing matters).
- Unit tests should mock Redis entirely (no real Redis connection in CI/unit
  tests) — same "mock the external dependency" pattern used throughout
  `training_engine/tests/` for TRL/HF components.

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] `training_engine/utils/callbacks.py` — `MetricsCallback(TrainerCallback)`
- [ ] Publishes to a clearly-named Redis pub/sub channel on each
      `on_log`/`on_evaluate`/`on_step_end` (whichever HF callback hooks are
      appropriate) with a payload matching `fine_tune_jobs`' live metric
      column names
- [ ] Redis client config read via the same pattern other `training_engine`
      modules use for environment/config (check `utils/hf_datasets.py` and
      `trainers/base_trainer.py` for precedent — there is no
      `pydantic-settings` Settings class in `training_engine` today)
- [ ] Unit tests mock the Redis client — no real network/Redis in tests
- [ ] `uv run ruff check .` and `uv run pytest tests/` clean in
      `training_engine/`

## STEPS TO COMPLETE

### Step 1 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-007-metrics-callbacks
```

### Step 2 — Implement callbacks.py + tests

### Step 3 — Verify
`(cd training_engine && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/)`

### Step 4 — Stage, commit, push

### Step 5 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-006)
Completed 2026-06-21. Built `training_engine/trainers/orpo_trainer.py` —
`ORPOTrainer` subclass of `BaseTrainer` directly (not `DPOTrainer` — siblings,
since ORPO needs no reference model, only `beta` per `job_service.py`'s
required keys). Reused DPO's `prepare_preference_rows()`/`REQUIRED_PAIR_KEYS`
validation pattern verbatim (duplicated, not imported). Confirmed via live
GitHub fetch of the pinned `trl==0.8.6` source (trl not installed locally)
that `trl.ORPOTrainer.__init__` takes no `beta`/`max_length`/
`max_prompt_length`/`ref_model` as direct kwargs — those live on an
`ORPOConfig` (subclass of `TrainingArguments`) passed as `args=`. Added
`_build_orpo_args()` + lazy-import helpers `_get_trl_orpo_trainer()`/
`_get_trl_orpo_config()`. `train()` loads exactly one model (no ref_model,
unlike DPO). 5 new tests in `test_orpo_trainer.py` (rejects non-orpo
methodology, rejects missing beta, rejects pair row missing keys, train()
asserts single model load + correct `ORPOConfig` kwargs + no direct
`ref_model`/`beta` to `ORPOTrainer` + callbacks passed through); full suite
59/59 passing; ruff clean. Pushed `feat/PHASE2-006-orpo-trainer`.
