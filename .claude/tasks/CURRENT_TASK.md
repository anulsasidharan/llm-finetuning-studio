# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-006
## TASK NAME: training_engine/trainers/orpo_trainer.py
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-006-orpo-trainer

## OBJECTIVE
Per CLAUDE.md section 2 and the Phase 2 backlog — build the ORPO trainer as a
subclass of `BaseTrainer`. Wire `trl.ORPOTrainer` for single-pass SFT +
preference alignment on chosen/rejected pairs (no reference model, unlike
DPO), validating `beta` in `training_config` (mirrors `job_service.py`'s
required keys for `methodology="orpo"`).

## CONTEXT FROM PHASE2-005
- `DPOTrainer` in `dpo_trainer.py` subclasses `BaseTrainer` directly (no LoRA
  requirement — `job_service.py`'s `METHOD_SPECIFIC_REQUIRED_KEYS["dpo"]` is
  just `{"beta"}`). It loads **two** model copies via `load_model()` (policy +
  frozen reference) and passes both to `trl.DPOTrainer(model=..., ref_model=...)`.
- DPO/ORPO dataset rows are preference pairs `{"prompt", "chosen", "rejected"}`,
  NOT ChatML messages — `BaseTrainer.prepare_dataset_rows()`/`to_chatml()` only
  handle alpaca/sharegpt/chatml single-conversation rows and do **not** apply.
  `dpo_trainer.py` added its own `prepare_preference_rows()` that validates
  `REQUIRED_PAIR_KEYS = ("prompt", "chosen", "rejected")` directly on raw rows
  instead. Reuse this same validation approach for ORPO (same pair shape).
- `job_service.py`'s `METHOD_SPECIFIC_REQUIRED_KEYS["orpo"]` is also `{"beta"}`
  — same single required key as DPO, no lora_r/lora_alpha.
- `trl==0.8.6` is pinned in `training_engine/requirements.txt`. ORPO in this
  version is `trl.ORPOTrainer(model=..., args=ORPOConfig-or-TrainingArguments,
  train_dataset=..., tokenizer=...)` — **no `ref_model`/`beta`-as-init-kwarg
  like DPOTrainer**; ORPO's odds-ratio term uses `training_args`-level config
  instead (check the installed `trl` source/signature directly before wiring,
  same as was done for DPOTrainer — `trl` is NOT installed in this dev env,
  confirmed via `python -c "import trl"` failing with `ModuleNotFoundError`,
  so signature must be confirmed via web docs/source inspection, not a live
  import).
- `utils/hf_datasets.py` must be used before any `from trl import ...`.
- Unit tests mock TRL/HF components — no real GPU/network.

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] `training_engine/trainers/orpo_trainer.py` — `ORPOTrainer` class
- [ ] Validates `beta` at init; loads chosen/rejected pair dataset (reuse the
      `prepare_preference_rows()` pattern from `dpo_trainer.py`)
- [ ] `train()` runs with mocked HF/TRL components in unit tests
- [ ] `uv run ruff check .` and `uv run pytest tests/` clean in `training_engine/`

## STEPS TO COMPLETE

### Step 1 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-006-orpo-trainer
```

### Step 2 — Implement orpo_trainer.py + tests

### Step 3 — Verify
`(cd training_engine && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/)`

### Step 4 — Stage, commit, push

### Step 5 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-005)
Completed 2026-06-21. Built `training_engine/trainers/dpo_trainer.py` — `DPOTrainer`
subclass of `BaseTrainer` (not `LoRATrainer` — DPO needs no LoRA per
`job_service.py`'s required keys, only `beta`). Loads policy model + a separate
frozen reference model copy via two `load_model()` calls, wires both into
`trl.DPOTrainer(model=, ref_model=, beta=, max_length=, max_prompt_length=...)`.
Dataset rows are validated as `{"prompt", "chosen", "rejected"}` pairs directly
(new `prepare_preference_rows()`/`REQUIRED_PAIR_KEYS`) since `to_chatml()`
doesn't apply to preference pairs. 5 new tests in `test_dpo_trainer.py`
(rejects non-dpo methodology, rejects missing beta, rejects pair row missing
keys, train() wires ref_model + trl kwargs correctly, callbacks passed
through); full suite 54/54 passing; ruff clean. Pushed `feat/PHASE2-005-dpo-trainer`.
