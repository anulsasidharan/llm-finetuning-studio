# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-007
## TASK NAME: Frontend: Evaluation Playground — side-by-side comparison
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-007-eval-playground

## NEXT TASK
Pick the next item from BACKLOG.md PHASE 3 — Cloud, Evaluation & Deploy.
PHASE3-008 (training_engine/export/merge_lora.py) is next in sequence and only
depends on PHASE2 complete, so it's unblocked.

## SUMMARY (this session, 2026-06-25)
**Scope grew beyond "frontend only"**: PHASE3-006 left `POST /eval/compare` and
`POST /eval/benchmark` unbuilt on the backend (training_engine's `compare.py`/
`benchmark.py` were standalone modules with no FastAPI wiring). Two
`AskUserQuestion` decisions were made before writing code (per the standing
"don't guess on open design questions" rule):
1. The backend gap had to be closed in this task, not deferred or mocked.
2. Eval jobs are dispatched via **Celery to training_engine's existing
   `gpu_training` queue** (mirrors `fine_tune_jobs`/`dispatch_training_job`
   exactly) — NOT a direct `apps/backend` import of
   `training_engine.evaluation`. A direct import was the first option offered
   and initially picked, but importing `training_engine.evaluation` would
   require adding torch/transformers/lm-eval-harness to
   `apps/backend/requirements.txt`, reversing the PHASE2-009 "DO NOT REVISIT"
   decision that training_engine is a standalone process never imported into
   apps/backend. Flagging this back to the user surfaced the real tradeoff and
   the Celery-dispatch route was chosen instead, preserving the architecture
   decision at the cost of larger scope (new DB table + two-process wiring
   instead of a thin synchronous route).

**New `eval_jobs` Postgres table** (migration `8f2c1a6e4d3b`, head was
`5d716f49b7ac`): `id, user_id, eval_type ("compare"|"benchmark"), status
(pending/queued/running/completed/failed), base_model_id,
finetuned_model_id (nullable — compare only), prompts (JSONB, compare only),
benchmarks (JSONB), num_fewshot, sample_limit, max_new_tokens (compare only),
result (JSONB), error_message, created_at, updated_at`. No WebSocket hub for
eval (unlike training jobs) — the frontend polls `GET /eval/{eval_id}`
instead, since there's no live per-step progress to stream (eval jobs run to
completion in one shot, not step-by-step like training).

**Backend** (mirrors the fine_tune_jobs dispatch pattern exactly):
- `models/eval_job.py`, `schemas/eval.py` (`EvalCompareCreate`,
  `EvalBenchmarkCreate`, `EvalJobResponse`)
- `services/eval_service.py` — duplicates `SUPPORTED_BENCHMARKS = {"mmlu",
  "hellaswag", "arc"}` from `training_engine/evaluation/benchmark.py`'s
  `BENCHMARK_TASKS` keys (same port-pattern as `dataset_format.py`) so invalid
  benchmark names 422 before a Celery round-trip
- `tasks/eval_tasks.py` — `dispatch_eval_job` (queue `"training"`, added to
  `core/celery_app.py`'s `task_routes`): marks `eval_jobs.status="queued"` via
  raw psycopg2, then `celery.send_task("training_engine.tasks.run_eval_job",
  queue="gpu_training", ...)` — no training_engine import, no Redis
  status_change publish (no WS consumer for eval)
- `api/v1/routes/eval.py` — `POST /eval/compare`, `POST /eval/benchmark`,
  `GET /eval` (list, scoped to user), `GET /eval/{eval_id}` (404 if not
  owned), registered in `api/v1/__init__.py`
- `models/user.py` gained `eval_jobs` relationship

**training_engine**:
- `utils/eval_status.py` — `mark_eval_running/completed/failed`, mirrors
  `utils/job_status.py` but simpler (no `MetricsPersistCallback` — eval jobs
  have no step-by-step metrics to persist, no `publish_status_change` — no WS
  hub for eval)
- `tasks.py` gained `run_eval_job` (`training_engine.tasks.run_eval_job`):
  routes on `eval_type` to `evaluation.compare.compare_models()` or
  `evaluation.benchmark.run_benchmark()`, marks running before dispatch,
  catches any exception generically (both `CompareError`/`BenchmarkError` are
  `ValueError` subclasses and real model-load/generation failures both need
  the same "mark failed with this message" handling) and persists the full
  `result` dict to Postgres on success

**Frontend**:
- Regenerated `openapi/schema.json` + `types/api-schema.d.ts`
  (`npm run generate:types`); added clean aliases to `types/index.ts`
  (`EvalJobResponse`, `EvalCompareCreate`, `EvalBenchmarkCreate`, `EvalType`,
  `EvalJobStatus`, `EvalBenchmark`)
- `hooks/useEval.ts` — `useEvalJobs`, `useEvalJob` (polls every 3s via
  `refetchInterval` while status is pending/queued/running, stops on a
  terminal status — this is the *only* live-update mechanism since there's no
  WS hub), `useCreateCompareJob`, `useCreateBenchmarkJob`
- `app/(dashboard)/evaluation/page.tsx` — Tabs (Compare / Benchmark forms) +
  a "Recent evaluations" table linking into the detail page. Base model picked
  from `useModelCatalog()` via `Select` (same pattern as `ConfigBuilder.tsx`);
  fine-tuned model is a free-text `Input` (no model registry/deploy-export
  manager exists yet — PHASE3-009/011 — so there's nothing to select from).
  Benchmarks are toggleable `Button` chips (no Checkbox component exists in
  `components/ui/`)
- `app/(dashboard)/evaluation/[evalId]/page.tsx` — status badge, polls via
  `useEvalJob`, renders side-by-side completions table (compare), a
  base/finetuned/delta metrics table (compare+benchmarks), or a flat metrics
  table (benchmark-only). `result: Record<string, unknown>` is narrowed with
  hand-written `asRecord`/`asCompletions`/`flattenNumericMetrics` helpers
  (same narrow-don't-assume pattern as the PHASE2-012 experiments page) —
  `flattenNumericMetrics` recurses to handle lm-eval's nested `arc` shape
  (`{arc_easy: {...}, arc_challenge: {...}}`) generically rather than special-
  casing it
- Sidebar already had an "Evaluation" nav entry pointing at `/evaluation`
  (added in an earlier session, unused until now)

**Verification**:
- `training_engine`: 135/135 tests passing (was 131 + 4 new in
  `test_tasks.py` for `run_eval_job`), `ruff check`/`ruff format --check`
  clean (one real reformat needed and applied in `utils/eval_status.py` +
  `tasks.py` — not just CRLF drift)
- `apps/backend`: 183/183 tests passing (was 175 + 8 new across
  `test_eval_routes.py`/`test_eval_tasks.py`), `ruff check` clean,
  `ruff format --check` clean for all new/touched eval files (2 real
  reformats applied in `test_eval_routes.py`/`eval_service.py`)
- Alembic migration applied cleanly against the local dev Postgres
  (`5d716f49b7ac` → `8f2c1a6e4d3b`)
- Live end-to-end smoke test against a real local backend (uvicorn on a throwaway
  port) + real local Postgres/Redis/MinIO: registered a user, created both a
  `compare` and a `benchmark` eval job via curl, confirmed rows persisted with
  `status="pending"` (no worker running to consume the `gpu_training` queue,
  expected), `GET /eval` and `GET /eval/{id}` round-tripped correctly. Test
  user cleaned up afterward.
- `npm run build` (TypeScript pass) and `npm run lint` clean — `/evaluation`
  and `/evaluation/[evalId]` both appear in the build's route list. Live dev
  server smoke test on a throwaway port: `/evaluation` returns 200 with
  "Evaluation Playground"/"Compare"/"Benchmark" in the HTML;
  `/evaluation/<uuid>` returns 200 with the "Loading evaluation..." shell
  (client-side fetch happens after hydration, consistent with every other
  detail page in this app)
- No browser-automation tool available in this environment (standing gotcha,
  confirmed again) — full interactive click-through of the Compare/Benchmark
  tabs, benchmark chip toggling, and polling-driven re-render on job
  completion could not be visually verified. The `compare_models`/
  `run_benchmark` calls themselves were never exercised against a real GPU
  worker in this session (no training_engine Celery worker process was
  started) — confirmed only that the dispatch chain (`dispatch_eval_job` →
  `celery.send_task` → DB row queued) works, mirroring exactly how
  PHASE2-009's training-job dispatch was verified without a real GPU worker.

## GOTCHAS LOGGED (see MEMORY.md for full detail)
- Initial plan to import `training_engine.evaluation` directly into
  `apps/backend` was caught and reversed via `AskUserQuestion` before any code
  was written — flagged because it would have silently violated the
  PHASE2-009 "DO NOT REVISIT" architecture decision. Worth re-checking this
  list before reaching for an "easy" synchronous shortcut on any future
  backend task that touches training_engine functionality.
- `eval_jobs` has no WebSocket hub and no per-step metrics — this was a
  deliberate scope decision (eval jobs aren't iterative like training), not an
  oversight. If a future task wants live progress during a long-running
  benchmark sweep, that would need new design, not just copy-pasting the
  training_metrics pub/sub pattern.
