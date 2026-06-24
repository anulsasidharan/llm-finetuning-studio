# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-015
## TASK NAME: Frontend Cost Estimator page
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-015-cost-estimator (not yet cut)

## OBJECTIVE
Per BACKLOG.md and CLAUDE.md's Core Capabilities list — build the
Cost Forecaster: pre-flight cost estimation before any training job, at
`app/(dashboard)/cost-estimator/page.tsx`.

## CONTEXT FROM PRIOR SESSIONS
- **PHASE2-014 (GPU Selector) deliberately did NOT build `POST /gpu/estimate`**
  even though CLAUDE.md section 5 lists it alongside `/gpu/instances` and
  `/gpu/pricing` — that route's real cost-projection logic (estimated hours ×
  price, possibly factoring num_epochs/dataset size from training_config) is
  this task's natural home, not the GPU Selector's. Build it now as part of
  this task: `schemas/gpu.py` would gain a `CostEstimateRequest`/
  `CostEstimateResponse` pair, `services/gpu_service.py` gains an
  `estimate_cost(...)` function, `api/v1/routes/gpu.py` gains
  `POST /gpu/estimate`. Re-run `scripts/export_openapi.py` +
  `npm run generate:types` afterward (same pipeline used in PHASE2-014).
- `apps/backend/schemas/gpu.py` already has `GpuPricingResponse(id, vendor,
  gpu_type, vram_gb, price_per_hour_usd)` and `services/gpu_service.py` has
  `list_instances(db, vendor=None)` / `get_pricing(vendor, gpu_type, db)` —
  reuse `get_pricing` internally for the estimate lookup rather than
  duplicating the query.
- `apps/frontend/hooks/useGPUPricing.ts` (calls `GET /api/v1/gpu/instances`)
  and `components/gpu/{GPUCard,VendorFilter,CostCard}.tsx` already exist from
  PHASE2-014 — `CostCard.tsx` today does a **client-side-only** multiplication
  (`price_per_hour_usd * hours`) for fixed 1hr/8hr/24hr/1-week projections, no
  backend call. Decide whether this task replaces that with a real
  `POST /gpu/estimate` call (e.g. factoring `num_epochs`/dataset size into an
  actual training-duration estimate, which client-side multiplication cannot
  do) or keeps `CostCard` as-is and adds a separate, more detailed estimator
  page. Don't guess — confirm scope with the user before writing code if it's
  not obvious from how `fine_tune_jobs.estimated_cost_usd` is meant to be
  populated.
- `app/(dashboard)/cost-estimator/` is an **empty directory** (no files yet) —
  same "scaffold built ahead of pages" pattern as `gpu-selector/` was before
  PHASE2-014.
- `ConfigBuilder.tsx`'s "Compute (optional)" card now has a "Compare GPUs"
  button (`Button render={<Link href="/gpu-selector" />}`) — consider whether
  this task adds a similar link/CTA to `/cost-estimator`, and whether cost
  estimation should happen *before* job creation (pre-flight, per CLAUDE.md)
  by reading the in-progress form's `gpu_type`/methodology/num_epochs via
  query params, mirroring how `/gpu-selector` and `/methodology` both write
  query params that `ConfigBuilder` reads back.
- No browser-automation tool is available in this environment (confirmed
  repeatedly through PHASE2-014) — expect the same verification fallback:
  `npm run lint`/`npm run build`, curl against a local backend, and the
  SSR-HTML-check fallback for anything client-interaction-only.

## PREVIOUS TASK SUMMARY (PHASE2-014)
Completed 2026-06-24. Built backend-to-frontend from a blank slate (no GPU
routes existed yet), mirroring `models.py`'s catalog pattern:

**Backend:** `schemas/gpu.py` (`GpuPricingResponse`), `services/gpu_service.py`
(`list_instances(db, vendor=None)` — full list ordered by price ascending,
optional vendor filter; `get_pricing(vendor, gpu_type, db)` — single-row
lookup, 404 via `NotFoundError` if missing), `api/v1/routes/gpu.py`
(`GET /instances?vendor=`, `GET /pricing?vendor=&gpu_type=`), registered in
`api/v1/__init__.py` under `/gpu` prefix. Deliberately did **not** build
`POST /gpu/estimate` — judged that real cost-projection math belongs to
PHASE2-015 (Cost Estimator)/PHASE3-003 (Cost Forecaster service), not the
GPU browsing/comparison page. 6 new tests in `tests/test_gpu_routes.py`
(list, vendor-filter, pricing-found, pricing-404, both require-auth) — full
backend suite 132/132 passing locally (required spinning up `docker compose
up -d postgres redis minio` since no containers existed yet this session,
then `alembic upgrade head` against the fresh DB, then
`scripts/seed_data.py`).

**Frontend:** `hooks/useGPUPricing.ts` (TanStack Query wrapping
`GET /api/v1/gpu/instances`), `components/gpu/GPUCard.tsx` (selectable card,
same selected-state pattern as `MethodologyCard`), `components/gpu/
VendorFilter.tsx` (button toggle group, "All vendors" + one button per
distinct vendor from the fetched data), `components/gpu/CostCard.tsx` (pure
client-side `price_per_hour_usd × hours` for 1hr/8hr/24hr/1-week — no backend
call, see note above for PHASE2-015 to revisit), `components/gpu/
GPUSelector.tsx` (holds `selectedVendor`/`selectedKey` state, renders
VendorFilter + GPUCard grid + CostCard for the selection, "Continue to
training config" button doing `router.push(`/config?gpu_type=...&cloud_vendor=...`)`
— same query-param-handoff pattern PHASE2-013 established for methodology).
New `app/(dashboard)/gpu-selector/page.tsx` (no longer an empty directory).

**Closed the loop into Config Builder:** `ConfigBuilder.tsx` now also reads
`gpu_type`/`cloud_vendor` from `useSearchParams()` to seed those two form
defaults (same `?? DEFAULT_VALUES.x` fallback pattern as methodology). The
"Compute (optional)" card's copy changed from "full GPU selection lands in a
future task" to a "Compare GPUs" button (`Button render={<Link
href="/gpu-selector" />}` — base-ui `render` prop, not `asChild`, per the
standing codebase convention) alongside the existing plain-text gpu_type/
cloud_vendor inputs (kept as a manual-override fallback, not removed).

Verified end-to-end against a live backend (not just `npm run build`): with
containers up and `seed_data.py` run, curled `GET /gpu/instances` (returned
all 10 seeded rows sorted by price ascending), `GET /gpu/instances?vendor=AWS`
(returned only the 2 AWS rows), and `GET /gpu/pricing?vendor=RunPod&gpu_type=A100-80GB`
(returned the single matching row) with a real JWT. `npm run build` clean,
`/gpu-selector` prerenders as a static `○` route; SSR HTML for that route
contains the page heading/copy (data itself is client-fetched, not in static
HTML, same as every other React-Query-driven page in this app). `npm run
lint` clean except the one pre-existing unrelated `ConfigBuilder.tsx`
React Compiler warning. Test users created during manual curl verification
were cleaned up via `docker exec fts_postgres psql ... DELETE FROM users`.
Not yet committed — branch `feat/PHASE2-014-gpu-selector` was already
checked out at session start per the git status snapshot.
