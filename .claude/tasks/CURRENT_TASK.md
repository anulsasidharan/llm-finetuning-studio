# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-005
## TASK NAME: training_engine/trainers/dpo_trainer.py
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-005-dpo-trainer

## OBJECTIVE
Per CLAUDE.md section 2 and the Phase 2 backlog — build the DPO trainer as a
subclass of `BaseTrainer`. Wire `trl.DPOTrainer` for preference alignment on
chosen/rejected pairs, validating `beta` in `training_config` (mirrors
`job_service.py`'s required keys for `methodology="dpo"`).

## CONTEXT FROM PHASE2-004
- `QLoRATrainer` in `qlora_trainer.py` subclasses `LoRATrainer` and overrides
  `load_model()` with `BitsAndBytesConfig` before inheriting the LoRA SFT pipeline.
- `utils/hf_datasets.py` must be used before any `from trl import ...`.
- `TrainerConfig` carries `beta` for DPO/ORPO; backend requires it for
  `methodology="dpo"`.
- Unit tests mock TRL/HF components — no real GPU/network.

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] `training_engine/trainers/dpo_trainer.py` — `DPOTrainer` class
- [ ] Validates `beta` at init; loads chosen/rejected pair dataset
- [ ] `train()` runs with mocked HF/TRL components in unit tests
- [ ] `uv run ruff check .` and `uv run pytest tests/` clean in `training_engine/`

## STEPS TO COMPLETE

### Step 1 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-005-dpo-trainer
```

### Step 2 — Implement dpo_trainer.py + tests

### Step 3 — Verify
`(cd training_engine && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/)`

### Step 4 — Stage, commit, push

### Step 5 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-004)
Completed 2026-06-21. Built `training_engine/trainers/qlora_trainer.py` — `QLoRATrainer`
subclass of `LoRATrainer` applying `BitsAndBytesConfig` 4-bit NF4 before PEFT LoRA
adapters, reusing the ChatML SFT pipeline from `LoRATrainer`. Validates
`lora_r`/`lora_alpha` at init. 4 new tests in `test_qlora_trainer.py`; full suite
49/49 passing; ruff clean. Pushed `feat/PHASE2-004-qlora-trainer`.
