# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE4-005
## TASK NAME: RLHF support — PPOTrainer + RewardTrainer (stretch goal)
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 4, Week 13
## BRANCH: feat/PHASE4-005-rlhf-support

## NEXT TASK
PHASE4-006 (Production Docker Compose — docker-compose.prod.yml).

## SUMMARY (this session, 2026-06-26)
Implemented end-to-end RLHF training in the GPU worker: preference-pair dataset
(``prompt``/``chosen``/``rejected``, same shape as DPO/ORPO) → RewardTrainer
fine-tune from ``training_config.reward_model_id`` → PPOTrainer policy optimisation
on ``base_model_id`` scored by the trained reward model.

**Training engine files created:**
- `training_engine/trainers/rlhf_trainer.py` — `RLHFTrainer`: phase 1
  `trl.RewardTrainer` (`AutoModelForSequenceClassification`, tokenized pairs) saves
  to `{output_dir}/reward_model`; phase 2 `trl.PPOTrainer`
  (`AutoModelForCausalLMWithValueHead` + ref model) manual generate→score→step loop,
  saves policy to `{output_dir}/final`.

**Training engine files modified:**
- `training_engine/tasks.py` — `TRAINER_CLASSES["rlhf"] = RLHFTrainer`; removed
  unsupported-methodology comment.
- `training_engine/trainers/__init__.py` — export `RLHFTrainer`.

**Backend files modified:**
- `apps/backend/tasks/training_tasks.py` — removed `UNSUPPORTED_METHODOLOGIES`
  block for `rlhf`; dispatch now queues RLHF jobs like other methodologies.

**Trigger points:**
1. Job created with `methodology=rlhf` + `reward_model_id` in `training_config` →
   `dispatch_training_job` marks `queued` → `run_training_job` → `RLHFTrainer.train()`.
2. Dispatch-time failure only when no dataset attached (unchanged).

**Verification:**
- `uv run pytest` — `test_rlhf_trainer.py` 5/5, `test_tasks.py` 10/10,
  `test_training_tasks.py` 8/8.
- `uv run ruff check` — clean on all touched files.
- No live GPU RLHF run tested (stretch goal; unit tests mock TRL/transformers).

## GOTCHAS LOGGED
- RLHF dataset must be preference pairs (`prompt`/`chosen`/`rejected`), not ChatML
  messages — same as DPO/ORPO; `BaseTrainer.prepare_dataset_rows`/`to_chatml` not used.
- `reward_model_id` is the RewardTrainer starting checkpoint (sequence-classification
  head, `num_labels=1`); after phase 1 the fine-tuned RM at `{output_dir}/reward_model`
  scores PPO generations.
- PPO uses TRL 0.8.6's manual loop (`generate` → reward score → `step`), not
  `Trainer.train()` — callbacks attach to RewardTrainer only.
- `PPOConfig.steps` derived from `num_epochs` × dataset prompt count (not a separate
  config key); `mini_batch_size`/`batch_size` adjusted for TRL divisibility constraint.
- Backend no longer rejects `rlhf` at dispatch — failures surface from trainer validation
  (missing `reward_model_id`, bad pair rows) inside the GPU worker.
