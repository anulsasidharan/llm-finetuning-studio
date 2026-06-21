# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-003
## TASK NAME: training_engine/trainers/lora_trainer.py
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-003-lora-trainer

## OBJECTIVE
Per CLAUDE.md section 2 and the Phase 2 backlog — build the LoRA trainer as a
subclass of `BaseTrainer`. Wire `peft.LoraConfig` + `trl.SFTTrainer` for
low-rank adapter training on a frozen base model, reusing the ChatML dataset
pipeline from `SFTTrainer`.

## CONTEXT FROM PHASE2-002
- `SFTTrainer` in `sft_trainer.py` is the reference implementation for TRL wiring.
- `utils/hf_datasets.py` must be used before any `from trl import ...` (HF
  `datasets` naming collision with local `training_engine/datasets/`).
- `TrainerConfig` already carries `lora_r` and `lora_alpha` from the flat backend
  config; `job_service.py` requires both for `methodology="lora"`.
- Unit tests mock TRL/PEFT/HF components — no real GPU/network.

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] `training_engine/trainers/lora_trainer.py` — `LoRATrainer` class extending `BaseTrainer`
- [ ] Applies `peft.LoraConfig` + `get_peft_model` before TRL SFTTrainer
- [ ] `train()` runs with mocked HF/PEFT/TRL components in unit tests
- [ ] `uv run ruff check .` and `uv run pytest tests/` clean in `training_engine/`

## STEPS TO COMPLETE

### Step 1 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-003-lora-trainer
```

### Step 2 — Implement lora_trainer.py + tests

### Step 3 — Verify
`(cd training_engine && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/)`

### Step 4 — Stage, commit, push

### Step 5 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-002)
Completed 2026-06-20. Built `training_engine/trainers/sft_trainer.py` — `SFTTrainer`
subclass wiring `trl.SFTTrainer` for full-weight SFT on ChatML-normalized rows;
added `utils/hf_datasets.py` to resolve the HF `datasets` naming collision before
TRL import. Returns status/metrics/model paths; saves to `{output_dir}/final`. 3 new
tests in `test_sft_trainer.py`; full suite 41/41 passing; ruff clean. Pushed
`feat/PHASE2-002-sft-trainer`.
