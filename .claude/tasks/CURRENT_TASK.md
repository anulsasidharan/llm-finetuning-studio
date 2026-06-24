# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-015
## TASK NAME: Frontend Cost Estimator page
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-015-cost-estimator

## NEXT TASK
Phase 2 (Training Engine + Core Modules) is now complete — all of PHASE2-001
through PHASE2-015 are ✅ DONE in BACKLOG.md. Pick the next item from
PHASE 3 — Cloud, Evaluation & Deploy (Weeks 9–12), e.g. PHASE3-001 (GPU
pricing service — RunPod + Lambda Labs API integration) or PHASE3-003 (Cost
forecaster service — pre-flight cost calculation, which can now build on this
session's `POST /gpu/estimate` heuristic rather than starting from scratch).

## SUMMARY (this session, 2026-06-24)
Resolved the one open scope question from CURRENT_TASK's prior draft via
`AskUserQuestion`: user chose to migrate GPU Selector's `CostCard.tsx` to the
new real backend estimate endpoint too, not just build a separate page.

**Backend** (`schemas/gpu.py`, `services/gpu_service.py`,
`api/v1/routes/gpu.py`, `tests/test_gpu_routes.py`):
- `CostEstimateRequest`/`CostEstimateResponse` schemas. Request supports two
  mutually exclusive shapes via a `@model_validator`: direct `hours`, or all
  four of `num_epochs`/`dataset_row_count`/`batch_size`/
  `gradient_accumulation_steps` together (422 if neither shape is satisfied).
- `gpu_service.estimate_cost()` reuses the existing `get_pricing()` (404 if
  vendor/gpu_type unknown), then either uses `hours` directly or computes
  `total_steps = ceil(dataset_row_count * num_epochs / (batch_size *
  gradient_accumulation_steps))` × a heuristic `SECONDS_PER_STEP_BY_METHODOLOGY`
  constant per methodology (sft=3.0, lora=1.8, qlora=2.2, dpo=3.5, orpo=3.0,
  rlhf=6.0, default=2.5) — made-up plausible numbers, not real benchmarks;
  flagged for PHASE3-001/PHASE3-003 to eventually replace with measured
  throughput. Had to `float()`-cast `GpuPricing.price_per_hour_usd` before
  arithmetic — asyncpg returns `decimal.Decimal` for the NUMERIC column even
  though the Pydantic response field is typed `float`.
- `POST /gpu/estimate` route, same auth/db-dependency pattern as the other two
  GPU routes. 5 new tests (hours-mode, training-params-mode, missing-params-422,
  not-found-404, requires-auth) — full backend suite 137/137 passing.
- Re-ran `scripts/export_openapi.py` + `npm run generate:types`; added
  `CostEstimateRequest`/`CostEstimateResponse` aliases to `types/index.ts`.

**Frontend:**
- `hooks/useCostEstimate.ts` — `useCostEstimate()` mutation (single estimate
  call) + `useCostProjections(instance, hoursList)` query (parallel fixed-hour
  estimates, used by `CostCard`).
- `components/gpu/CostCard.tsx` — migrated off client-side `price × hours`
  math to `useCostProjections`, falling back to the old local multiplication
  only while the request is in flight (`isLoading`) for no-flicker UX.
- `components/gpu/CostEstimatorForm.tsx` (new) — RHF+Zod form: vendor →
  gpu_type cascading selects (from `useGPUPricing`), methodology select,
  optional dataset select (auto-fills `dataset_row_count` from the dataset's
  real `row_count` via `useEffect`+`setValue`, stays editable), num_epochs/
  batch_size/gradient_accumulation_steps numeric inputs. Submits to
  `useCostEstimate`, renders a result card (estimated hours + cost).
- `app/(dashboard)/cost-estimator/page.tsx` (new) — wraps the form in
  `<Suspense>` (required for `useSearchParams`, same Next.js 16 rule as
  `/config`). Already linked in `Sidebar.tsx`'s nav (pre-existing).
- `ConfigBuilder.tsx`'s "Compute (optional)" card gained a second "Estimate
  cost" button next to "Compare GPUs", building its href live from `watch()`
  on all the relevant in-progress form fields via `URLSearchParams`.
  `CostEstimatorForm` reads those same param names back to prefill itself —
  same bidirectional query-param handoff pattern as `/gpu-selector`↔`/config`
  and `/methodology`↔`/config`.

**Verification:** Backend 137/137 pytest passing locally (containers were
already up from a prior session). `npm run build` clean (`/cost-estimator`
prerenders static), `npm run lint` clean except one new but harmless
`watch()`-can't-be-memoized React Compiler warning in `CostEstimatorForm.tsx`
(same pre-existing class as `ConfigBuilder.tsx`'s). Live end-to-end: seeded
`gpu_pricing`, curled `POST /gpu/estimate` in both modes against a running
uvicorn (hours-mode: RunPod A100-80GB × 8hr @ $1.89/hr → $15.12;
training-params-mode: LoRA/5000 rows/3 epochs/batch 4 → 1.875h → $3.54;
confirmed 422 on incomplete params). Ran `npm run build && npm run start`,
curled SSR HTML for both `/cost-estimator` and `/gpu-selector` (200, correct
headings) to confirm the `CostCard` migration didn't regress the existing
page. Test user and both background servers cleaned up afterward.

Not yet committed — branch `feat/PHASE2-015-cost-estimator` was already
checked out at session start.

## GOTCHAS LOGGED (see MEMORY.md for full detail)
- The Bash tool's cwd leak (not just PowerShell's) — a bare `cd apps/backend
  && cmd` in one Bash call leaked into the next call and broke the lint hook.
  Use `(cd apps/backend && cmd)` subshell syntax instead.
