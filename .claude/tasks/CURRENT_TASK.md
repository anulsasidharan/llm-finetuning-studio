# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-010
## TASK NAME: training_engine/export/export_gguf.py
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-010-export-gguf

## NEXT TASK
PHASE3-011 (Frontend: Deploy & Export Manager page) — depends on PHASE3-009 (done).

## SUMMARY (this session, 2026-06-25)
Implemented `training_engine/export/export_gguf.py` — standalone module that
converts any local HuggingFace model directory to GGUF format by invoking
llama.cpp's `convert_hf_to_gguf.py` script via subprocess.

**Design decisions:**
- `export_gguf(model_dir, output_dir, *, quantization_type="q4_k_m", llama_cpp_path=None, model_name=None)`
  is the single public entry point — same flat-function style as `merge_lora.py` and `push_hf.py`
- Uses subprocess rather than importing llama.cpp Python libs — llama.cpp
  is a C++ project; its Python conversion script is the standard industry
  interface for HF→GGUF conversion, not a pip package
- Script path resolution: `llama_cpp_path` kwarg (file or repo-root dir)
  > `LLAMA_CPP_CONVERT_SCRIPT` env var > raises ExportGGUFError with
  a helpful message
- `_run_convert_subprocess(cmd)` is a thin wrapper around `subprocess.run`
  so tests can mock it without touching the stdlib directly
- Output filename: `<model_name>-<quantization_type>.gguf`; `model_name`
  defaults to `model_dir.name` so no manual naming is required
- `SUPPORTED_QUANT_TYPES` frozenset (f32/f16/q8_0/q6_k/q5_k_m/q5_0/
  q4_k_m/q4_0/q3_k_m/q2_k) — validated before subprocess is launched
- `ExportGGUFError(ValueError)` — consistent with `MergeLoRAError`, `PushHFError`
- No lazy import helper needed — `subprocess` is stdlib, always available

**Verification:**
- 11 unit tests in `tests/test_export_gguf.py`:
  - 5 error paths: missing model_dir, unsupported quant type, no script
    configured, invalid llama_cpp_path, env var pointing to missing file
  - 1 subprocess-failure path: non-zero returncode raises ExportGGUFError
  - 5 happy paths: full success (verifies cmd args), custom model_name,
    llama_cpp_path as directory, script from env var, all 10 quant types
- Full suite (excluding pre-existing langdetect + torch trainer failures):
  148 → 159 passing (11 new)
- `ruff check` and `ruff format --check` both clean
- Pre-commit hook passed (ruff lint + format stages)

## GOTCHAS LOGGED
- The pre-existing langdetect import failure in test_quality_check.py
  (ModuleNotFoundError: No module named 'langdetect') continues to block
  that file from collection — unchanged, not introduced by this task.
- Pre-existing trainer test failures (9 tests across test_base_trainer,
  test_dpo_trainer, test_lora_trainer, test_qlora_trainer, test_sft_trainer)
  also unchanged.
