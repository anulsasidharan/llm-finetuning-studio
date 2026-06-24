# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-002
## TASK NAME: GPU pricing Redis cache with TTL
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-002-gpu-pricing-cache

## NEXT TASK
Pick the next item from BACKLOG.md PHASE 3 — Cloud, Evaluation & Deploy. Natural
next step is PHASE3-003 (Cost forecaster service — pre-flight cost calculation,
can build on `gpu_service.estimate_cost()` from PHASE2-015) or PHASE3-004 (Cloud
launcher — submit jobs to RunPod via API, builds on PHASE3-001's RunPod provider
client).

## SUMMARY (this session, 2026-06-24)
Wrapped `POST /gpu/sync-pricing` / `gpu_pricing_sync_service.sync_live_pricing()`
with a Redis TTL cache, using the `GPU_PRICING_CACHE_TTL_SECONDS` setting that
had been declared-but-unused in `core/config.py` since PHASE1.

**Design decision**: cache the *sync operation's result*, not the `GET
/gpu/instances` / `GET /gpu/pricing` read endpoints. Those already read cheaply
from the local `gpu_pricing` Postgres table — there's nothing expensive to
debounce there. The real cost/risk is `sync_live_pricing()` calling RunPod's and
Lambda Labs' real (rate-limited) third-party APIs; the cache exists to stop
repeated `POST /gpu/sync-pricing` calls (multiple users clicking it, an
overlapping cron job, etc.) from re-hitting those APIs more than once per
`GPU_PRICING_CACHE_TTL_SECONDS` (3600s default).

**Implementation** (`apps/backend/services/gpu_pricing_sync_service.py`):
- Single Redis key `CACHE_KEY = "gpu_pricing:sync_result"` — there's only ever
  one "current" sync result, so no per-vendor or per-request keying needed.
- `sync_live_pricing(db, *, redis_client=None)` gained the optional
  `redis_client` kwarg (mirrors the existing `httpx.AsyncClient` injection
  pattern in the provider modules) — if omitted, it opens its own
  `redis.asyncio.Redis.from_url(settings.REDIS_URL)` (the main app's db-0 cache,
  not `TRAINING_PUBSUB_DB`'s db-3 pub/sub channel) and closes it via `aclose()`
  in a `finally` block.
- On every call: check cache first (`GET` the key, `model_validate_json` it back
  into a `GpuPricingSyncResponse`, return a copy with `cached=True`). On a miss,
  run the real provider-fetch + dedupe + upsert pipeline unchanged, then cache
  the fresh `GpuPricingSyncResponse` (`cached=False`) via `SETEX`-equivalent
  (`SET ... ex=settings.GPU_PRICING_CACHE_TTL_SECONDS`).
- Both cache read and write failures are caught and `structlog.warning`-logged,
  never raised — same risk-tolerance pattern as every other Redis touchpoint in
  this codebase (`websocket/training_hub.py`, `tasks/training_tasks.py`,
  `training_engine/utils/callbacks.py`): a Redis outage must degrade to
  "always call the real providers," not break the sync endpoint.
- `schemas/gpu.py`'s `GpuPricingSyncResponse` gained `cached: bool = False` so
  callers (and tests) can tell a cache hit from a fresh sync.
- `scripts/sync_gpu_pricing.py`'s log line now also reports `cached=result.cached`.

**Test isolation gotcha**: all `POST /gpu/sync-pricing` tests in
`test_gpu_pricing_sync.py` share one global Redis key, so an earlier test's
cached response could leak into a later test and short-circuit its fake
provider — added a `clear_gpu_pricing_cache` fixture (sync `redis.Redis`,
deletes `CACHE_KEY` before and after) and applied it to every existing test that
calls the sync endpoint, plus the 2 new cache-specific tests.

**New tests** (2, both via the real route + real local Redis, same precedent as
the rest of this file — no fakeredis dependency added):
- `test_sync_pricing_second_call_served_from_cache` — first call hits the fake
  provider (`cached=False`), second call returns the identical body except
  `cached=True`, and asserts the fake provider's call counter stayed at 1.
- `test_sync_pricing_cache_ttl_matches_configured_setting` — asserts
  `redis.ttl(CACHE_KEY)` is `0 < ttl <= settings.GPU_PRICING_CACHE_TTL_SECONDS`
  after a sync call.

**Verification**: full backend suite 148/148 passing (146 existing + 2 new) —
ran locally via `uv run pytest tests/` with the standard local-env Postgres/Redis
overrides documented in MEMORY.md. `ruff check .` clean, no new
`ruff format --check .` drift beyond the same pre-existing CRLF/LF noise already
flagged before this session (confirmed via `git stash` + re-check). One real
fix made mid-session: `redis.asyncio.Redis.close()` is deprecated in `redis==5.0.4`
in favor of `aclose()` — switched to avoid a `DeprecationWarning` on every
self-owned-client call.

Re-ran `scripts/export_openapi.py` + `npm run generate:types`; no `types/index.ts`
changes needed since its `GpuPricingSyncResponse` alias already re-exports
whatever the generated schema has — `npx tsc --noEmit` clean. No frontend page
consumes `POST /gpu/sync-pricing` yet (confirmed via grep), so no UI changes
needed — this stays backend-only, same scoping precedent as PHASE3-001.

Did **not** add a force-refresh/cache-bypass query param to the route — out of
scope for what this task asked for ("wrap ... with a
GPU_PRICING_CACHE_TTL_SECONDS-keyed Redis cache"). Flag this if a future task
needs an admin override before the TTL expires.

Not yet committed — branch `feat/PHASE3-002-gpu-pricing-cache` was already
checked out at session start.

## GOTCHAS LOGGED (see MEMORY.md for full detail)
- The PostToolUse lint hook's `ruff --fix` runs after *every* `Edit`/`Write`,
  not just at the end — splitting "add an import" and "add the usage of that
  import" into two separate Edit calls lets ruff's unused-import fix delete
  the import in between, silently breaking the file until the next edit
  re-adds it. Hit this again this session adding `import redis` +
  `from services.gpu_pricing_sync_service import CACHE_KEY` to
  `test_gpu_pricing_sync.py` — fixed by re-adding both imports together with
  their first real usage (the new `clear_gpu_pricing_cache` fixture) in one
  Edit call.
- A leaked Bash `cd` into `apps/backend` breaks the lint hook's relative path
  resolution to `.claude/hooks/lint.py` (it looks for that path under the
  *current* cwd, not the repo root) — surfaces as a `[Errno 2] No such file or
  directory` PostToolUse error on the *next* Edit, unrelated to that edit's own
  correctness. Fix: run a bare `cd <repo-root> && pwd` Bash call to reset cwd
  before the next Edit.
