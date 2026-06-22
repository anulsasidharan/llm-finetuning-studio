# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-011
## TASK NAME: Frontend Live Training Dashboard with WebSocket charts
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-011-training-dashboard (not yet cut)

## OBJECTIVE
Per BACKLOG.md and CLAUDE.md's Core Capabilities list — build the Live Training
Dashboard: a frontend page at `app/(dashboard)/training/[jobId]/page.tsx` that connects
to the now-built `WS /ws/training/{job_id}` (PHASE2-010) and renders real-time loss
curves, GPU utilization, and live job status as messages arrive.

## CONTEXT FROM PRIOR SESSIONS
- The WebSocket hub is live: `apps/backend/websocket/training_hub.py` (`WS
  /ws/training/{job_id}`), confirmed working end-to-end this session via a real backend
  + `redis-cli PUBLISH` + the `websockets` pip package. Auth is **JWT as a query param**
  (`?token=<access_token>`) — the frontend must read the access token the same way
  `lib/api.ts`'s `getAccessToken()` does (`fts_access_token` in `localStorage`) and
  append it to the WS URL itself; there is no header-based option.
- Two payload `type`s arrive on the same socket, already implemented and tested:
  `metrics_update` (`step`, `epoch`, `train_loss`, `eval_loss`, `gpu_utilization_pct`,
  `vram_used_gb`, `tokens_per_second`) and `status_change` (`status`). The frontend needs
  to branch on `type` and update different UI state for each.
  - Backend: `dispatch_training_job` publishes `status_change` for `queued`/`failed`.
  - training_engine: `run_training_job`/`utils/job_status.py` publish `status_change` for
    `running`/`completed`/`failed`, and `MetricsCallback` publishes `metrics_update`.
- An unauthenticated or unauthorized (wrong user / nonexistent job) WS connection
  attempt gets a clean **HTTP 403 at the handshake** — confirmed live, not just in
  mocked tests. The frontend's WS client should handle this connection failure
  gracefully (e.g. show an error state), not just silently retry forever.
- CLAUDE.md's directory structure lists `components/charts/{LossChart,LRScheduleChart,
  GPUUtilChart,VRAMChart,ThroughputChart}.tsx` and `lib/websocket.ts` — none of these
  exist yet. No chosen charting library is pinned in `apps/frontend/package.json` yet
  either — this is a real open decision (recharts/visx/chart.js/etc. all plausible,
  given shadcn/ui's own chart components are recharts-based).
- `apps/frontend/hooks/useJobs.ts` (PHASE1-WEEK3-012) already has a `useJob(jobId)`
  query for the static `FineTuneJobResponse` — useful for the dashboard's initial state
  (methodology, base_model_id, current persisted status/metrics) before the socket has
  delivered anything live, but has no WebSocket logic itself.
- `app/(dashboard)/config/[jobId]/page.tsx` (PHASE1-WEEK3-012) is a read-only job detail
  view using `JobStatusBadge`/`TrainingControls` — worth checking before deciding whether
  the new training dashboard route is a separate page or extends that one.
- No browser-automation tool is available in this environment (confirmed repeatedly
  across prior sessions) — verifying the live chart rendering/WS reconnect behavior will
  need the same fallback pattern as before: `npm run lint`/`npm run build`, real backend
  + `redis-cli PUBLISH` + inspecting server-rendered HTML, and if needed a temporary
  Node script exercising the real WS client module directly (deleted before committing).

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] Pick and add a charting library (or confirm reuse of an existing one) — flag as an
      open decision before coding
- [ ] `lib/websocket.ts` — a small client wrapping `WebSocket` (or a hook) that builds
      the authed WS URL, parses incoming JSON, and exposes `metrics_update`/
      `status_change` events to consumers
- [ ] `app/(dashboard)/training/[jobId]/page.tsx` (or extend the existing
      `config/[jobId]` page — open decision) showing live status + at least a loss chart
- [ ] Chart components under `components/charts/` for whichever subset of metrics this
      task actually wires up (loss curve at minimum; GPU/VRAM/throughput if time allows)
- [ ] Graceful handling of WS connection failure / job already completed (no further
      messages will ever arrive)
- [ ] `npm run lint`/`npm run build` clean

## STEPS TO COMPLETE

### Step 1 — Confirm the charting library and exact page/route placement with the user
before writing code (both are genuine open decisions, not guessable from existing code).

### Step 2 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-011-training-dashboard
```

### Step 3 — Implement lib/websocket.ts + chart components + the dashboard page

### Step 4 — Verify
`(cd apps/frontend && npm run lint && npm run build)`, plus live verification against a
real backend + `redis-cli PUBLISH` per the established pattern.

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-010)
Completed 2026-06-22. Confirmed two scope forks with the user before coding: (1) WS auth
— user picked JWT as a query param, reusing `core.auth.decode_token`; (2) whether to add
`status_change` Redis publishing to PHASE2-009's job-status transitions now — user
picked yes.

Built `apps/backend/websocket/connection_manager.py` (per-job_id connection registry)
and `websocket/training_hub.py` (`WS /ws/training/{job_id}`, wired into `main.py` at the
top level, not under `/api/v1`). Auth closes with code 1008 before `accept()` on any
failure. The relay loop lives in a separately-callable `_serve()`, split out because
`TestClient.websocket_connect()`'s teardown cancels the whole ASGI task group ahead of
any handler cleanup `await`s — caught via a failing assertion, not by inspection.

Added `publish_status_change()` to `training_engine/utils/callbacks.py`, wired into
`utils/job_status.py`'s three `mark_job_*` functions, plus a duplicate
`_publish_status_change()` in `apps/backend/tasks/training_tasks.py` (process-boundary
duplicate, can't import training_engine) wired into its `queued`/`failed` transitions —
realizes the payload-type split reserved since PHASE2-007.

Verified live end-to-end: real backend + real `fts_redis`/`fts_postgres`, registered a
user, created a real job (`.delay()` now succeeds against the broker once
`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND` are also overridden to `localhost:6380` for
local runs — new gotcha, see MEMORY.md), connected with the real `websockets` pip
package, `redis-cli PUBLISH`'d both payload types into `training_metrics:{job_id}` on
Redis db 3, confirmed both arrived verbatim over the real socket, and confirmed an
unauthenticated connection gets a clean HTTP 403 at the handshake.

16 new tests in `apps/backend` (6 connection_manager, 7 training_hub including a
deterministic `_serve()` unit test driven via `asyncio.run()` instead of `TestClient`,
3 new in test_training_tasks.py) + 8 in `training_engine` (4 `publish_status_change`,
4 status-change wiring) — `apps/backend` 112/112, `training_engine` 111/111 passing.

Pushed `feat/PHASE2-010-websocket-hub`; PR not opened (manual creation per established
workflow).
