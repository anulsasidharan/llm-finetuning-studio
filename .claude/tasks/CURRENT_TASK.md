# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-004
## TASK NAME: training_engine/trainers/qlora_trainer.py
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-004-qlora-trainer

## OBJECTIVE
Per CLAUDE.md section 2 and the Phase 2 backlog — build the QLoRA trainer as a
subclass of `LoRATrainer` (or `BaseTrainer`). Wire `BitsAndBytesConfig` for 4-bit
NF4 quantization plus `peft.LoraConfig` + `trl.SFTTrainer` for low-rank adapter
training on a quantized frozen base, reusing the ChatML dataset pipeline.

## CONTEXT FROM PHASE2-003
- `LoRATrainer` in `lora_trainer.py` is the reference for PEFT + TRL SFT wiring.
- `utils/hf_datasets.py` must be used before any `from trl import ...`.
- `TrainerConfig` carries `lora_r` and `lora_alpha`; backend requires both for
  `methodology="qlora"`.
- Unit tests mock TRL/PEFT/BitsAndBytes/HF components — no real GPU/network.

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] `training_engine/trainers/qlora_trainer.py` — `QLoRATrainer` class
- [ ] Applies `BitsAndBytesConfig` (4-bit NF4) before PEFT LoRA adapters
- [ ] `train()` runs with mocked HF/PEFT/TRL/BnB components in unit tests
- [ ] `uv run ruff check .` and `uv run pytest tests/` clean in `training_engine/`

## STEPS TO COMPLETE

### Step 1 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-004-qlora-trainer
```

### Step 2 — Implement qlora_trainer.py + tests

### Step 3 — Verify
`(cd training_engine && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/)`

### Step 4 — Stage, commit, push

### Step 5 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-003)
Completed 2026-06-21. Built `training_engine/trainers/lora_trainer.py` — `LoRATrainer`
subclass applying `peft.LoraConfig` + `get_peft_model` on a frozen base before
`trl.SFTTrainer`; reuses ChatML dataset pipeline from `SFTTrainer`. Validates
`lora_r`/`lora_alpha` at init. Default target modules for LLaMA-style architectures;
`lora_dropout=0.05`. 4 new tests in `test_lora_trainer.py`; full suite 45/45 passing;
ruff clean. Pushed `feat/PHASE2-003-lora-trainer`.
