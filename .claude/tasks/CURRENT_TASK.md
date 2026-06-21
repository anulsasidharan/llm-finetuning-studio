# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-002
## TASK NAME: training_engine/trainers/sft_trainer.py
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-002-sft-trainer

## OBJECTIVE
Per CLAUDE.md section 2 and the Phase 2 backlog — build the SFT (Supervised Fine-Tuning)
trainer as the first concrete subclass of `BaseTrainer`. Wire `trl.SFTTrainer` to run full
weight updates on the base model using ChatML-normalized dataset rows from
`prepare_dataset_rows()`.

## CONTEXT FROM PHASE2-001
- `BaseTrainer` accepts the flat `training_config` dict from the backend and normalizes it
  via `TrainerConfig.from_dict()`.
- Dataset rows are passed pre-loaded (`dataset_rows: list[dict]`) — no HF `datasets` loader yet.
- `load_model()` / `load_tokenizer()` / `build_training_arguments()` / `get_callbacks()` live
  on the base class; SFT uses the default full-precision `load_model()` (no PEFT).
- `prepare_dataset_rows()` normalizes to ChatML via `datasets.formatter.to_chatml`.
- `train()` must return a dict with status + output paths/metrics (shape TBD by sft_trainer).

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] `training_engine/trainers/sft_trainer.py` — `SFTTrainer` class extending `BaseTrainer`
- [ ] `train()` runs `trl.SFTTrainer` with mocked HF components in unit tests (no real GPU/network)
- [ ] `uv run ruff check .` and `uv run pytest tests/` clean in `training_engine/`

## STEPS TO COMPLETE

### Step 1 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-002-sft-trainer
```

### Step 2 — Implement sft_trainer.py + tests

### Step 3 — Verify
`(cd training_engine && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/)`

### Step 4 — Stage, commit, push

### Step 5 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-001)
Completed 2026-06-20. Built `training_engine/trainers/base_trainer.py` — abstract `BaseTrainer`
with `TrainerConfig.from_dict()` normalizing the flat backend config, pre-loaded `dataset_rows`,
`load_tokenizer`/`load_model`/`build_training_arguments`/`prepare_dataset_rows`/`get_callbacks`,
and abstract `train()`. Scope: flat config normalized internally; rows pre-loaded (no HF
`datasets` import); device placement in base, quantization deferred to QLoRA subclass. 11 new
tests in `test_base_trainer.py`; full suite 38/38 passing; ruff clean. Pushed
`feat/PHASE2-001-base-trainer`.
