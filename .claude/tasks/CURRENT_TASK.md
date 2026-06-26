# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-008
## TASK NAME: training_engine/export/merge_lora.py
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-008-merge-lora

## NEXT TASK
PHASE3-009 (training_engine/export/push_hf.py) — depends on PHASE3-008 (now done).

## SUMMARY (this session, 2026-06-25)
Implemented `training_engine/export/merge_lora.py` — standalone module that merges a
PEFT LoRA/QLoRA adapter back into its base model, producing a fully self-contained
merged model ready for deployment/export (used by push_hf and export_gguf downstream).

**Design decisions:**
- `merge_lora(adapter_dir, output_dir, *, base_model_id=None, trust_remote_code=False)`
  is the single public entry point — mirrors the flat-function style of
  `evaluation/compare.py`/`evaluation/benchmark.py` (no class needed for a one-shot
  operation)
- `base_model_id` inferred from `adapter_config.json`'s `base_model_name_or_path` when
  not supplied explicitly — PEFT saves this automatically during `trainer.save_model()`,
  so callers don't need to thread it through from the job record if they already have the
  adapter dir
- `merged_model_dir = output_dir / "merged"` — one level below the provided output_dir
  (mirrors LoRATrainer's `output_dir / "final"` pattern)
- `MergeLoRAError(ValueError)` — consistent with `TrainerError`, `CompareError`,
  `BenchmarkError` elsewhere in training_engine
- Heavy imports (peft, torch, transformers) are all lazy via `_get_peft_model_cls()` and
  `_load_base_model_and_tokenizer()` — same testability pattern as all trainers; neither
  package is installed in the dev env so tests mock them entirely
- No Celery task wired yet — intentionally deferred to PHASE3-011 (Deploy & Export
  Manager) when all three export modules (merge_lora, push_hf, export_gguf) are complete
  and a single export pipeline can be designed together

**Verification:**
- 6 new unit tests in `tests/test_merge_lora.py` — 3 error-path tests (missing
  adapter_dir, missing adapter_config.json, no base_model_id) + 3 happy-path tests
  (full merge flow, explicit base_model_id overrides config, trust_remote_code passthrough)
- Full suite: 141/141 passing (was 135 + 6 new)
- `ruff check` and `ruff format --check` both clean on new files
- Pre-commit hook passed (ruff lint + format stages)

## GOTCHAS LOGGED
- None new — the hook path error (`training_engine/.claude/hooks/lint.py not found`)
  is the standing CWD-mismatch gotcha from PHASE1-WEEK3-006/013, not a new regression.
  The actual ruff pre-commit stage (run by git commit hook from repo root) passed cleanly.
