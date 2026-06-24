# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-001
## TASK NAME: GPU pricing service — RunPod + Lambda Labs API integration
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-001-gpu-pricing-service

## NEXT TASK
Pick the next item from BACKLOG.md PHASE 3 — Cloud, Evaluation & Deploy. Natural
next step is PHASE3-002 (GPU pricing Redis cache with TTL — wrap the new
`POST /gpu/sync-pricing` / `gpu_pricing_sync_service.sync_live_pricing()` with a
`GPU_PRICING_CACHE_TTL_SECONDS`-keyed Redis cache, already declared unused in
`core/config.py` since PHASE1), or PHASE3-003 (Cost forecaster service, which can
build on `gpu_service.estimate_cost()` from PHASE2-015).

## SUMMARY (this session, 2026-06-24)
Built live GPU pricing integration for RunPod + Lambda Labs, on top of the
existing static `gpu_pricing` table (seeded by `scripts/seed_data.py`).

**Verified real API shapes before writing any code** (per the PHASE2-006
lesson — never assume a third-party API shape from training data) by pulling
the real source of `runpod-python`'s GraphQL queries
(`runpod/api/queries/gpus.py`, `runpod/api/graphql.py`) and skypilot's
`fetch_lambda_cloud.py` data fetcher via `gh api`/WebFetch:
- **RunPod**: `POST https://api.runpod.io/graphql`, `Authorization: Bearer
  <key>`, GraphQL query `gpuTypes { id displayName memoryInGb securePrice
  communityPrice }` — `securePrice`/`communityPrice` are real `GpuType`
  fields, confirmed via the SDK's per-id query even though its own list-all
  query doesn't request them.
- **Lambda Labs**: `GET https://cloud.lambdalabs.com/api/v1/instance-types`,
  `Authorization: Bearer <key>` — returns `{"data": {<instance_name>:
  {"instance_type": {"price_cents_per_hour", "specs": {"gpus", "vcpus",
  "memory_gib"}}}}}`. No VRAM field — GPU model → VRAM is a hardcoded map
  (`GPU_VRAM_GB`) since the API never reports it. Multi-GPU instance types
  (e.g. `gpu_8x_a100_80gb_sxm4`) report the whole instance's price; divided by
  `specs.gpus` to get a true per-GPU hourly price comparable to the existing
  single-GPU `gpu_pricing` rows.

**New code** (`apps/backend/services/gpu_pricing_providers/`):
- `base.py` — `NormalizedGpuOffer` dataclass + `GpuPricingProviderError`.
- `runpod_provider.py` / `lambda_labs_provider.py` — each exposes one async
  `fetch_*_pricing(api_key, client=None)` using `httpx.AsyncClient` (already
  pinned, never previously used directly in this backend). Both accept an
  optional injected client for test mocking via `httpx.MockTransport`, and
  both raise `GpuPricingProviderError` on any HTTP/GraphQL-error/timeout
  failure — never let a provider outage propagate as an unhandled exception.
- `services/gpu_pricing_sync_service.py` — `sync_live_pricing(db)` calls both
  providers (reading `settings.RUNPOD_API_KEY`/`LAMBDA_LABS_API_KEY`, already
  declared-but-unused in `core/config.py`/`.env.example` since before this
  task), skips a vendor cleanly if its key is empty, catches
  `GpuPricingProviderError` per-vendor so one outage doesn't block the other,
  dedupes same-`(vendor, gpu_type)` offers keeping the cheapest, then upserts
  into `gpu_pricing` via the same `postgresql.insert(...).on_conflict_do_update`
  pattern `scripts/seed_data.py` already uses. Returns a per-vendor
  `ok`/`skipped`/`failed` summary + total rows upserted.
  - **Testability gotcha hit and fixed**: the vendor→fetch-function dispatch
    table must NOT capture direct function references at module-load time
    (`fetch_runpod_pricing` bound once into a dict) — that bakes in a
    reference `monkeypatch.setattr("services.gpu_pricing_providers.
    runpod_provider.fetch_runpod_pricing", ...)` can never reach. Fixed by
    importing the provider *modules* (`from services.gpu_pricing_providers
    import lambda_labs_provider, runpod_provider`) and wrapping each call in
    a lambda that does the attribute lookup at call time
    (`runpod_provider.fetch_runpod_pricing(api_key)`), so monkeypatching the
    provider module's attribute is honored. Flag this exact pattern if a
    future module builds a similar "registry of swappable async callables."
- `schemas/gpu.py` — added `GpuPricingSyncVendorResult`/`GpuPricingSyncResponse`.
- `api/v1/routes/gpu.py` — added `POST /gpu/sync-pricing` (same
  auth+db-dependency pattern as the other 3 GPU routes).
- `scripts/sync_gpu_pricing.py` — standalone one-shot script mirroring
  `seed_data.py`'s `sys.path.insert` bootstrap, for manual/cron use outside
  HTTP. Wired a `make sync-gpu-pricing` target alongside the existing `make
  seed`.
- Re-ran `scripts/export_openapi.py` + `npm run generate:types`; added
  `GpuPricingSyncResponse`/`GpuPricingSyncVendorResult` aliases to
  `types/index.ts`. No new frontend page — this task was backend-only per
  BACKLOG.md's own scoping (PHASE3-002 is the caching layer, PHASE3-003 the
  cost forecaster; neither built yet).

**Verification:** 9 new backend tests (5 provider unit tests mocking httpx via
`httpx.MockTransport`: RunPod price-fallback/GraphQL-error/HTTP-error, Lambda
Labs multi-GPU price division/HTTP-error; 4 route tests: requires-auth,
skips-vendor-without-key, upserts+reports-per-vendor-failure via monkeypatched
providers + real DB row assertions, dedupes-keeping-cheapest) — full backend
suite 146/146 passing. `ruff check .` clean; `ruff format --check .` flags 66
pre-existing files repo-wide (confirmed via `git status --short` none of them
are files this session touched — a pre-existing CRLF/format drift, not a
regression from this task). Frontend `npx tsc --noEmit` clean after the
type-codegen re-run.

Not yet committed — branch `feat/PHASE3-001-gpu-pricing-service` was already
checked out at session start.

## GOTCHAS LOGGED (see MEMORY.md for full detail)
- The PostToolUse lint hook's `ruff --fix` runs after *every* `Edit`/`Write`,
  not just at the end — splitting "add an import" and "add the usage of that
  import" into two separate Edit calls lets ruff's unused-import fix delete
  the import in between, silently breaking the file until the next edit
  re-adds it. Add an import and its first usage in the same Edit/Write call
  when possible, or expect to re-add the import afterward.
