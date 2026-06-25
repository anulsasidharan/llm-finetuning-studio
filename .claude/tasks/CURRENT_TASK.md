# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-005
## TASK NAME: training_engine/evaluation/benchmark.py — MMLU/HellaSwag/ARC
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-005-eval-benchmark

## NEXT TASK
Pick the next item from BACKLOG.md PHASE 3 — Cloud, Evaluation & Deploy. Natural
next step is PHASE3-006 (training_engine/evaluation/compare.py — base vs
fine-tuned), which can reuse `run_benchmark()`'s dual model_id/loaded-model
input directly. PHASE3-007 (Frontend Evaluation Playground) depends on
PHASE3-006.

## SUMMARY (this session, 2026-06-24)
**Scope**: a single standalone `training_engine/evaluation/benchmark.py`
module (not a `BaseTrainer` subclass — benchmarking isn't training), no
backend route/Celery wiring yet — same scoping precedent as PHASE2's trainer
classes (PHASE2-002 through 006) landing standalone before PHASE2-009 wired
any of them into a Celery task. `POST /eval/benchmark` (in CLAUDE.md's route
table) is not built; deferred to a future wiring task.

**Implementation**: `run_benchmark(*, benchmarks, model_id=None, model=None,
tokenizer=None, device=None, batch_size=8, num_fewshot=None, limit=None,
trust_remote_code=False)` wraps `lm-eval` (lm-evaluation-harness — already
pinned `lm-eval==0.4.2`/`evaluate==0.4.2` in requirements.txt since PHASE1,
never previously imported anywhere in this repo). Requires exactly one of
`model_id` (loads fresh via `lm_eval.models.huggingface.HFLM(pretrained=
model_id, ...)`) or both `model`+`tokenizer` (an already-loaded pair passed
straight into `HFLM(pretrained=<model instance>, tokenizer=..., ...)`) — this
dual-mode input is deliberate so PHASE3-006's compare.py can reuse it
unchanged to benchmark an in-memory fine-tuned model without round-tripping
through disk.

`BENCHMARK_TASKS = {"mmlu": ("mmlu",), "hellaswag": ("hellaswag",), "arc":
("arc_easy", "arc_challenge")}` maps friendly names to real lm-eval task/group
tags — verified by reading the actually-installed package's
`tasks/mmlu/default/_mmlu.yaml`/`tasks/arc/*.yaml` directly (lm_eval IS
pip-installed in this dev venv, unlike trl, so this was direct source
inspection, not a GitHub fetch — same "verify real third-party API shape
before coding" rule as PHASE2-006/PHASE3-001/PHASE3-004, just via a different
verification method this time). Calls `lm_eval.simple_evaluate(model=<HFLM
instance>, tasks=[...], num_fewshot=, batch_size=, device=, limit=,
log_samples=False)` and reshapes its flat `results["results"][task_name]`
dict into one entry per requested benchmark name (`arc` nests both
`arc_easy`/`arc_challenge` sub-dicts; `mmlu`/`hellaswag` are flat). New
`BenchmarkError(ValueError)` raised for: empty `benchmarks`, unknown benchmark
name, and neither/both of `model_id`/`model`+`tokenizer` supplied.

**Landmine hit and fixed**: `lm_eval` → `evaluate` → `from datasets import
Dataset` hits the exact same local-`datasets`-package naming collision
already flagged for `trl` (MEMORY.md, since PHASE1-WEEK3-002/PHASE2-002) —
confirmed live, a bare `import lm_eval` in this venv raises `ImportError:
cannot import name 'Dataset' from 'datasets'` pointing at the local package.
Fixed identically to every other TRL/PEFT-adjacent import in this codebase:
new lazy `_get_lm_eval()`/`_get_hflm_cls()` helpers in `benchmark.py` both
call the existing `utils.hf_datasets.ensure_hf_datasets_loaded()` before
importing `lm_eval`/`HFLM` — no change needed to `hf_datasets.py` itself, it
already generalizes to any HF-`datasets`-dependent import.

**Tests**: 10 new in `training_engine/tests/test_benchmark.py`, all mocking
`_get_lm_eval`/`_get_hflm_cls` entirely (never imports real `lm_eval`/loads a
real model) — rejects empty/unsupported benchmarks, rejects neither/both of
model_id vs loaded-model, constructs `HFLM` correctly for both input modes,
expands `arc` to two tasks and nests its metrics, passes `num_fewshot`/`limit`
through, defaults device via `_resolve_device()` when not given, missing task
in raw results defaults to `{}`.

**Verification**: full training_engine suite 121/121 passing (111 prior + 10
new), `ruff check .` clean, `ruff format --check .` shows only the same
pre-existing CRLF/LF drift across unrelated files already flagged in
MEMORY.md/prior sessions — neither new file (`evaluation/benchmark.py`,
`tests/test_benchmark.py`) is in that list. `evaluation/__init__.py`
(previously an empty placeholder) now re-exports `BENCHMARK_TASKS`/
`BenchmarkError`/`run_benchmark`, mirroring `trainers/__init__.py`'s
re-export pattern.

Not yet committed — branch `feat/PHASE3-005-eval-benchmark` was already
checked out at session start.

## GOTCHAS LOGGED (see MEMORY.md for full detail)
- The "leaked Bash cwd breaks the `.claude/hooks/lint.py` PostToolUse hook"
  gotcha (logged repeatedly since PHASE2-014/PHASE2-015/PHASE3-002) recurred
  again this session after `cd training_engine/.venv/Lib/site-packages/
  lm_eval && ...` to inspect the installed package's real source — reset with
  a plain `cd <repo-root> && pwd` each time, reactively, same as PHASE3-002.
  Worth defaulting to the subshell form (`(cd dir && cmd)`) proactively next
  time to skip the extra round-trip, as already flagged in MEMORY.md.
