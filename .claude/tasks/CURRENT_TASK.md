# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-006
## TASK NAME: training_engine/evaluation/compare.py — base vs fine-tuned
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-006-eval-compare

## NEXT TASK
Pick the next item from BACKLOG.md PHASE 3 — Cloud, Evaluation & Deploy. Natural
next step is PHASE3-007 (Frontend: Evaluation Playground — side-by-side
comparison), which depends on PHASE3-006 (this task) and should call into a
future `POST /eval/compare` backend route — no backend route exists yet for
either `compare.py` or `benchmark.py`, deferred per the established
PHASE2-002-through-006 standalone-module-before-Celery-wiring precedent.
Alternatively, PHASE3-008 (training_engine/export/merge_lora.py) is also
unblocked (only depends on PHASE2 complete) if frontend work isn't next.

## SUMMARY (this session, 2026-06-24)
**Scope**: a single standalone `training_engine/evaluation/compare.py` module
(not a `BaseTrainer` subclass, same precedent as `benchmark.py`), no backend
route/Celery wiring — `POST /eval/compare` (CLAUDE.md's route table) remains
unbuilt, deferred to a future wiring task alongside `POST /eval/benchmark`.

**Implementation**: `compare_models(*, prompts, base_model_id=None,
base_model=None, base_tokenizer=None, finetuned_model_id=None,
finetuned_model=None, finetuned_tokenizer=None, benchmarks=None, device=None,
max_new_tokens=256, num_fewshot=None, limit=None, trust_remote_code=False)`
covers both halves of CLAUDE.md's "side-by-side base vs fine-tuned model
comparison with benchmarks" Evaluation Playground bullet in one function:

1. **Side-by-side generation** (always runs): each side (`base_*`/
   `finetuned_*`) accepts either a `*_model_id` (loaded fresh via a new
   `_load_model_and_tokenizer()`, mirrors `BaseTrainer.load_model()`/
   `load_tokenizer()`'s dtype/device-map logic but standalone since
   `compare.py` isn't a trainer) or an already-loaded `*_model`/`*_tokenizer`
   pair — same dual-input contract `run_benchmark()` uses (validated by a new
   `_resolve_side()` helper, one call per side, parameterized by a `label`
   string so the `CompareError` message names the right side). Generates one
   completion per prompt from each side via `model.generate()` (device read
   back off the model itself via `next(model.parameters()).device`, not the
   resolved comparison device — robust to a caller-supplied already-loaded
   model living on a different device than `_load_model_and_tokenizer()`
   would have picked). Returns `completions: [{prompt, base_completion,
   finetuned_completion}, ...]`.
2. **Benchmark deltas** (only when `benchmarks` is given): calls the existing
   `run_benchmark()` (PHASE3-005) **twice**, once per side, passing each
   side's already-loaded model/tokenizer via `run_benchmark`'s loaded-model
   branch (`model=`/`tokenizer=` kwargs) — deliberately avoids letting
   `run_benchmark` reload either model from disk a second time when the
   caller supplied a `model_id`, since `compare_models` already loaded it for
   generation. A new `_diff_metrics()` recursively computes
   finetuned-minus-base deltas for numeric leaves shared by both sides'
   metrics dicts (handles `arc`'s nested `{arc_easy: {...}, arc_challenge:
   {...}}` shape from `benchmark.py`'s `_extract_metrics()` the same way it
   handles flat `mmlu`/`hellaswag` dicts). Result gains a `benchmarks: {base,
   finetuned, delta}` key only when requested — omitted entirely otherwise.

New `CompareError(ValueError)` raised only for: empty `prompts`, and
neither/both of `{label}_model_id`/`{label}_model`+`{label}_tokenizer`
supplied, for either side independently.

**Tests**: 10 new in `training_engine/tests/test_compare.py`, all mocking
`_load_model_and_tokenizer`/`_generate`/`run_benchmark` at the module boundary
(never imports real `torch`/`transformers` model loading or generation) —
rejects empty prompts, rejects neither/both model_id vs loaded-model
independently for each side, loads both sides and builds completions from
model_ids, skips loading entirely when both sides are pre-loaded, includes
`benchmarks.delta` only when `benchmarks` is passed (omitted key otherwise),
defaults device via `_resolve_device()` when not given, plus a direct
`_diff_metrics()` unit test for the nested-arc-style-dict case.

**Verification**: full training_engine suite 131/131 passing (121 prior + 10
new), `ruff check .` clean (one `UP038` violation caught and fixed —
`isinstance(x, (int, float))` → `isinstance(x, int | float)`), `ruff format
--check .` shows only the same pre-existing CRLF/LF drift across unrelated
files already flagged in MEMORY.md/PHASE3-005's summary — neither new file
(`evaluation/compare.py`, `tests/test_compare.py`) is in that list.
`evaluation/__init__.py` now also re-exports `CompareError`/`compare_models`
alongside the existing `BENCHMARK_TASKS`/`BenchmarkError`/`run_benchmark`.

Not yet committed — branch `feat/PHASE3-006-eval-compare` was already checked
out at session start.

## GOTCHAS LOGGED (see MEMORY.md for full detail)
- No new gotchas this session — the only landmine relevant to this module
  (lm_eval/`datasets` local-package naming collision) was already solved
  inside `benchmark.py`'s `_get_lm_eval()`/`_get_hflm_cls()`, reused unchanged
  via the existing `run_benchmark()` import; `compare.py` itself only touches
  `transformers`/`torch` directly (no `datasets`-dependent import), so the
  collision never triggers in this file.
