# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-003
## TASK NAME: Cost forecaster service — pre-flight cost calculation
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-003-cost-forecaster

## NEXT TASK
Pick the next item from BACKLOG.md PHASE 3 — Cloud, Evaluation & Deploy. Natural
next step is PHASE3-004 (Cloud launcher — submit jobs to RunPod via API, builds
on PHASE3-001's RunPod provider client) or PHASE3-005 (training_engine
evaluation/benchmark.py — MMLU/HellaSwag/ARC).

## SUMMARY (this session, 2026-06-24)
**Scope decision (asked the user via AskUserQuestion before coding, since
`POST /gpu/estimate` already does single vendor/GPU cost estimation and it
wasn't obvious what a "forecaster" should add on top):** the user picked
**multi-GPU comparison forecast only** — a new endpoint that, given training
params (no vendor/gpu_type required), returns a ranked cost estimate across
every matching `gpu_pricing` row, cheapest first. The alternative option
offered (auto-persisting `estimated_cost_usd` onto `FineTuneJob` at job-creation
time) was explicitly **not** chosen — that column still goes unset by
`job_service.create_job`; flag this as a still-open gap if a future task needs
it.

**New endpoint**: `POST /api/v1/gpu/forecast` (`apps/backend/api/v1/routes/gpu.py`).
- Request (`CostForecastRequest`, `schemas/gpu.py`): same `hours` XOR
  (`num_epochs`+`dataset_row_count`+`batch_size`+`gradient_accumulation_steps`+
  optional `methodology`) shape as `CostEstimateRequest`, but `vendor` is now
  optional (acts as a filter, not a required lookup key) and a new optional
  `min_vram_gb` filter was added. Shared the hours-or-training-params
  model_validator logic via a new `_check_hours_or_training_params(model)`
  free function in `schemas/gpu.py` rather than duplicating the validator body
  across both request classes.
- Response (`CostForecastResponse.options: list[CostForecastOption]`): one
  entry per matching `gpu_pricing` row (`vendor`, `gpu_type`, `vram_gb`,
  `price_per_hour_usd`, `estimated_hours`, `estimated_cost_usd`), sorted
  ascending by `estimated_cost_usd` — cheapest option is always `options[0]`.
  404s (`NotFoundError`) if the vendor/min_vram_gb filters match zero rows.
- New `apps/backend/services/cost_forecast_service.py` — queries `gpu_pricing`
  with optional `vendor`/`min_vram_gb` filters, computes one shared
  `estimated_hours` value (same for every option, since it doesn't depend on
  which GPU is chosen) and a per-row `estimated_cost_usd`.

**Refactor in `services/gpu_service.py`** to make the hours-estimation math
reusable without coupling it to `CostEstimateRequest` specifically: the old
private `_estimate_hours_from_training_params(payload)` (took the whole
request object) is now two pieces — `estimate_training_hours(**explicit kwargs)`
(pure function, the actual heuristic: total_steps × seconds_per_step_by_methodology
÷ 3600) and `resolve_estimated_hours(payload: CostEstimateRequest |
CostForecastRequest)` (picks `payload.hours` if set, else calls
`estimate_training_hours` with the payload's fields). `estimate_cost()` and the
new `forecast_cost()` both call `resolve_estimated_hours()` — single source of
truth for the heuristic, no duplicated math between the two endpoints.

**Tests** (6 new, all in `tests/test_gpu_routes.py` alongside the existing
`/gpu/estimate` tests, reusing the same `seeded_gpu_pricing` fixture): sorted
cheapest-first ordering, `min_vram_gb` filtering, training-params-based
estimate matches the same worked example as the existing `/gpu/estimate` test
(1000 rows × 3 epochs ÷ batch 4 = 750 steps × 1.8s/lora-step = 0.375h), 422 on
missing params, 404 on a vendor with no matching rows, 401 with no auth token.

**Verification**: full backend suite 154/154 passing (148 existing + 6 new),
`ruff check .` clean, no new `ruff format` drift beyond the same pre-existing
CRLF/LF noise already flagged in MEMORY.md/prior sessions. Re-ran
`scripts/export_openapi.py` + `npm run generate:types` (schema.json +
api-schema.d.ts changed, `types/index.ts` needed no edits since nothing
consumes the new types yet) — `npx tsc --noEmit` clean. No frontend page
calls `/gpu/forecast` — backend-only, same scoping precedent as PHASE3-001/002.

Not yet committed — branch `feat/PHASE3-003-cost-forecaster` was already
checked out at session start.

## GOTCHAS LOGGED (see MEMORY.md for full detail)
- Same PostToolUse lint-hook gotcha as PHASE3-002: splitting "add an import"
  from "add its usage" across two Edit calls lets ruff's unused-import fix
  silently delete the import in between. Hit it twice this session adding
  `CostForecastRequest`/`CostForecastResponse` + `cost_forecast_service` to
  `apps/backend/api/v1/routes/gpu.py` — fixed by re-adding the import together
  with the new `/forecast` route body in one Edit call.
