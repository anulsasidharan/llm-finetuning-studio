# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-004
## TASK NAME: Cloud launcher — submit jobs to RunPod via API
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-004-cloud-launcher

## NEXT TASK
Pick the next item from BACKLOG.md PHASE 3 — Cloud, Evaluation & Deploy. Natural
next step is PHASE3-005 (training_engine/evaluation/benchmark.py — MMLU/HellaSwag/ARC)
since PHASE3-004 was the last GPU/cloud-vendor item before evaluation work starts.

## SUMMARY (this session, 2026-06-24)
**Scope decisions (asked the user via AskUserQuestion before coding, since the
one-line backlog description left two real architecture choices open):**
1. **Launch trigger = new explicit endpoint**, not auto-fired inside job
   creation. `POST /api/v1/jobs/{job_id}/launch-cloud` is a separate call the
   frontend makes once the user is ready to actually provision the GPU —
   decoupled from `POST /jobs`, same precedent as PHASE3-003 explicitly NOT
   auto-wiring cost onto job creation. `job_service.create_job` is unchanged.
2. **Launch + terminate function**, scoped to "launch only" for the route.
   `services/cloud_launchers/runpod_launcher.py` has both `launch_runpod_pod()`
   and `terminate_runpod_pod()`, but only launch is wired to a route — no
   `DELETE /jobs/{id}` exists yet in this codebase, so terminate is ready for a
   future cancel-job task to call without touching the launcher module again.

**Design**: a launched RunPod pod just runs the existing `training_engine`
Celery worker image (already defined in `docker-compose.gpu.yml`), so it picks
up the exact same dispatch task already sent to the `"gpu_training"` queue by
`tasks/training_tasks.py::dispatch_training_job` — **no changes needed there**.
The cloud launcher's only job is provisioning the GPU pod itself.

**Verified the real RunPod GraphQL mutation shape before writing any code**
(per this repo's standing rule — see MEMORY.md's PHASE2-006 ORPO entry — never
guess a third-party API shape from training data when source is fetchable):
fetched `runpod/runpod-python`'s `runpod/api/mutations/pods.py` from GitHub via
WebFetch. Confirmed `podFindAndDeployOnDemand(input: {...})` field names
(`name`, `imageName`, `cloudType`, `gpuTypeId`, `gpuCount`, `containerDiskInGb`,
`volumeInGb`, `env: [{key, value}]`) and `podTerminate(input: { podId })`
(scalar return, no sub-selection). RunPod's GraphQL API has no public schema
doc, so the official SDK's own query-builder is the closest thing to a
contract test — see runpod_launcher.py's module docstring/comments.

**New `services/cloud_launchers/` package** (mirrors `gpu_pricing_providers/`'s
package shape): `base.py` (`LaunchedPod` dataclass, `CloudLauncherError`),
`runpod_launcher.py` (`launch_runpod_pod()`/`terminate_runpod_pod()` — builds
the mutation via inline string interpolation ported from runpod-python's own
approach, with quote-escaping added since the SDK's f-strings have none).

**`services/gpu_pricing_providers/runpod_provider.py` gained
`resolve_gpu_type_id(api_key, gpu_type, client=None) -> str`** — reverse-resolves
our normalized DB `gpu_pricing.gpu_type` string (e.g. `"A10080GBPCIe"`) back to
RunPod's raw GPU type id (e.g. `"NVIDIA A100 80GB PCIe"`), which the launch
mutation's `gpuTypeId` input requires verbatim. Needed because
`fetch_runpod_pricing` only keeps the normalized name for DB storage and
discards RunPod's raw `id` field. Refactored the shared HTTP/GraphQL call into
a new private `_fetch_raw_gpu_types()` so both functions reuse it — no
duplicated query string.

**New `services/cloud_launch_service.py`** — `launch_job(job: FineTuneJob) ->
LaunchedPod`: validates `cloud_vendor` is in `SUPPORTED_CLOUD_VENDORS =
{"RunPod"}` (only vendor with a real launch integration so far — Lambda
Labs/AWS/GCP/Azure still pricing-only, same one-vendor-at-a-time pattern as
PHASE2's trainers), validates `gpu_type` is set and `RUNPOD_API_KEY`/new
`TRAINING_ENGINE_DOCKER_IMAGE` setting are configured (all → `ValidationError`,
422), resolves the raw RunPod gpu_type_id, then launches — builds the pod's env
vars (`DATABASE_URL_SYNC`, `REDIS_URL`, `CELERY_BROKER_URL`,
`CELERY_RESULT_BACKEND`, `TRAINING_ENGINE_REDIS_URL`, `MINIO_*`,
`CUDA_VISIBLE_DEVICES=0`) so the launched pod's worker can reach this
deployment's own Postgres/Redis/MinIO and join the `gpu_training` queue exactly
like the local worker does.

**New exception class `core/exceptions.py::ExternalServiceError` (502)** — first
time this backend calls a third-party API where failure must surface as a real
HTTP error to an explicit caller action (not swallowed into a 200 partial-result
body like `gpu_pricing_sync_service` does for the multi-vendor sync). Both
`GpuPricingProviderError` (from `resolve_gpu_type_id`) and `CloudLauncherError`
(from `launch_runpod_pod`) map to this in `cloud_launch_service.launch_job`.
Picked up automatically by `main.py`'s existing `AppException` handler — no
main.py change needed (same as every other exception subclass, per MEMORY.md's
earlier exceptions gotcha).

**New route**: `POST /api/v1/jobs/{job_id}/launch-cloud` (`api/v1/routes/jobs.py`)
→ `schemas/job.py::CloudLaunchResponse` (`pod_id`, `image_name`, `machine_id`).
New `job_service.launch_cloud_job(job_id, user, db)` does the ownership-scoped
`get_job` lookup (404 if missing/not-owned) then delegates to
`cloud_launch_service.launch_job`.

**New setting**: `core/config.py::TRAINING_ENGINE_DOCKER_IMAGE: str = ""` — the
docker image tag the launched RunPod pod runs; empty by default (real value is
a deployment-time concern, not exercised in dev/test).

**Tests** (24 new, all mocked — no real RunPod calls):
- `test_gpu_pricing_providers.py`: 3 new for `resolve_gpu_type_id` (match
  found, no match raises, HTTP error raises). Refactored the duplicated runpod
  gpuTypes JSON fixture into one shared `_RUNPOD_GPU_TYPES_RESPONSE` module
  constant.
- `test_cloud_launchers.py` (new file): 6 tests for `launch_runpod_pod`/
  `terminate_runpod_pod` against `httpx.MockTransport` — success parses
  `pod_id`/`image_name`/`machine_id`, no-pod-returned raises, GraphQL errors
  raise, HTTP errors raise, terminate success, terminate GraphQL error raises.
- `test_cloud_launch_service.py` (new file): 7 tests for `launch_job` —
  unsupported vendor/missing gpu_type/missing API key/missing docker image all
  422 via `ValidationError`; success path asserts the exact `gpu_type_id`/
  `name`/`env["FTS_JOB_ID"]` passed through; both `GpuPricingProviderError` and
  `CloudLauncherError` map to `ExternalServiceError`.
- `test_job_routes.py`: 5 new for the route — success (200, mocks
  `job_service.cloud_launch_service.launch_job`), unsupported vendor (422, no
  mocking needed — real validation fires before any network call), not-found
  (404), other-user's-job scoped 404, unauthenticated 401.

**Verification**: full backend suite 175/175 passing (151 existing + 24 new),
`ruff check .` clean, `ruff format --check .` shows only the same pre-existing
CRLF/LF drift across unrelated files already flagged in MEMORY.md/prior
sessions — none of this session's new files are in that list. Re-ran
`scripts/export_openapi.py` + `npm run generate:types` (schema.json +
api-schema.d.ts changed to include `launch-cloud` + `CloudLaunchResponse`) —
`npx tsc --noEmit` clean. No frontend page calls `/jobs/{id}/launch-cloud` yet
— backend-only, same scoping precedent as PHASE3-001/002/003.

Not yet committed — branch `feat/PHASE3-004-cloud-launcher` was already
checked out at session start.

## GOTCHAS LOGGED (see MEMORY.md for full detail)
- Hit the "split import-from-usage across two Edits gets unused-import-stripped
  by the lint hook" gotcha **repeatedly** this session (worse than PHASE3-002/003's
  single hit) while wiring `job_service.py`'s new `launch_cloud_job` and
  `api/v1/routes/jobs.py`'s new route — every attempt to add the import in one
  Edit and the function/usage in a *separate* Edit call got the import silently
  removed in between, even when the calls were back-to-back in the same turn.
  The only reliable fix was using **Write with the complete final file
  content in one atomic operation** instead of Edit at all, once a file needed
  both a new import and new usage. Defaulting straight to Write (not Edit) the
  next time a change needs an import + its first usage added to an existing
  file would have saved several round-trips.
