# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-010
## TASK NAME: WebSocket hub — subscribe Redis channel, push to browser
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-010-websocket-hub (not yet cut)

## OBJECTIVE
Per BACKLOG.md — build the FastAPI WebSocket endpoint `WS /ws/training/{job_id}`
(CLAUDE.md section 5) that subscribes to the Redis pub/sub channel
`training_metrics:{job_id}` (published by `training_engine/utils/callbacks.py`'s
`MetricsCallback`, PHASE2-007) and relays each `metrics_update` payload to the
connected browser in real time. This is what the future Live Training Dashboard
(PHASE2-011) will connect to.

## CONTEXT FROM PRIOR SESSIONS
- `apps/backend/websocket/__init__.py` exists but is empty — no hub code yet.
  CLAUDE.md section 2 names the target files `websocket/training_hub.py` and
  `websocket/connection_manager.py`.
- Redis channel contract (already implemented, do not change without updating
  `training_engine/utils/callbacks.py` too): channel name `training_metrics:{job_id}`,
  payload `{"type": "metrics_update", "job_id", "step", "epoch", "train_loss",
  "eval_loss", "gpu_utilization_pct", "vram_used_gb", "tokens_per_second"}`. A sibling
  `"status_change"` payload type was reserved in PHASE2-007's docstring for whoever
  marks job status transitions — that's now `apps/backend/tasks/training_tasks.py` /
  `training_engine/tasks.py` (PHASE2-009), which currently only write to Postgres, not
  to this Redis channel. Decide whether `run_training_job`/`dispatch_training_job`
  should also publish a `"status_change"` event on each transition so a connected
  WebSocket client sees status flips live (not just metric updates) — flagged but not
  decided in PHASE2-009.
- Redis URL for this channel: backend reads it via `settings.REDIS_URL`/dedicated pubsub
  config (check `core/config.py`'s `TRAINING_PUBSUB_DB` — currently typed as `str` but
  unused anywhere; training_engine's publisher side uses `TRAINING_ENGINE_REDIS_URL`
  pointing at db `3`. Confirm both sides agree on the same Redis logical DB before
  wiring the subscriber.
- The async backend (`core/database.py` etc.) is asyncio-based — use `redis.asyncio`
  (already pinned `redis==5.0.4` includes the asyncio client) for the subscriber loop,
  not the sync `redis` client `MetricsCallback`/`MetricsPersistCallback` use on the
  training_engine side.
- No browser-automation tool available in this environment (confirmed PHASE1-WEEK3-009,
  still true) — verifying the live WebSocket relay end-to-end will need either a
  temporary Python `websockets` client script against a running `uvicorn` + a manual
  `redis-cli PUBLISH training_metrics:<job_id> '{...}'` test message, or unit tests
  against FastAPI's `TestClient.websocket_connect` with a mocked Redis subscriber.

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] `apps/backend/websocket/connection_manager.py` — tracks active WebSocket
      connections per `job_id`
- [ ] `apps/backend/websocket/training_hub.py` — `WS /ws/training/{job_id}` endpoint,
      subscribes to `training_metrics:{job_id}` on connect, relays messages, cleans up
      subscription + connection on disconnect
- [ ] Auth: decide whether the WebSocket route requires the same JWT auth as REST
      routes (e.g. token as a query param, since WS can't send an Authorization header)
- [ ] Unit tests mock the Redis subscriber — no real Redis pub/sub required in CI
- [ ] `ruff check`/`ruff format --check` clean in `apps/backend`

## STEPS TO COMPLETE

### Step 1 — Confirm auth approach + whether to add "status_change" publishing to
PHASE2-009's tasks (open questions above) with the user before writing code.

### Step 2 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-010-websocket-hub
```

### Step 3 — Implement connection_manager.py + training_hub.py + tests

### Step 4 — Verify
`(cd apps/backend && uv run ruff check . && uv run ruff format --check . && uv run pytest tests/)`

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-009)
Completed 2026-06-21. Resolved the process-boundary question (flagged for user
confirmation) with two explicit decisions: (1) training_engine runs as its own
standalone Celery worker process, matching docker-compose.gpu.yml's pre-existing
(previously unfinished) `celery -A worker.celery_app worker --queues=gpu_training`
service — not imported into apps/backend, since apps/backend/requirements.txt has none
of the heavy ML deps; (2) job status persistence is "coarse status + periodic metric
snapshots" into Postgres, not status-only.

Built `apps/backend/tasks/training_tasks.py` — `dispatch_training_job` Celery task
(queue `training`, registered name `tasks.training_tasks.dispatch_training_job`)
rejects `rlhf` (no trainer yet) and jobs with no dataset attached by marking the job
`failed` via a raw sync `psycopg2` UPDATE (no sync SQLAlchemy session — app code never
uses sync ORM sessions per the architecture decision; raw psycopg2 against
`DATABASE_URL_SYNC` mirrors the existing test/script pattern). On success, marks the
job `queued` and hands off via `celery.send_task("training_engine.tasks.run_training_job",
queue="gpu_training")` — calling a task by name with no Python import of
training_engine at all. `apps/backend/services/job_service.py`'s `create_job` now calls
`dispatch_training_job.delay(...)` right after commit, passing the job's own fields
plus (if a dataset is attached) its `storage_path`/`format` — chosen over having the
dispatch task re-query Postgres for the same data, since the async route already has it
in memory. New job creation still returns `status="pending"` synchronously (existing
tests unchanged) since `.delay()` only enqueues; the flip to `queued` happens
asynchronously once a worker consumes it.

Built `training_engine/worker.py` (the `celery_app` Celery instance the
docker-compose.gpu.yml command already referenced but never existed) and
`training_engine/tasks.py`'s `run_training_job` (registered name
`training_engine.tasks.run_training_job`) — downloads the dataset itself from MinIO via
new `training_engine/utils/storage.py` (own lazily-imported `Minio` client, training_engine
doesn't import `apps/backend/core/storage.py` per the standalone-process architecture
decision; bucket name passed was deliberately *not* added — training_engine reads
`BUCKET_DATASETS` from its own shared `.env` instead), looks up the trainer class in a
`TRAINER_CLASSES` dict (`rlhf` is simply absent, so it falls into the same "no trainer"
path as any unsupported value rather than crashing), wires three callbacks into the
trainer: `MetricsCallback` (Redis pub/sub, PHASE2-007) + new
`utils/job_status.MetricsPersistCallback` (same `on_log`/`on_evaluate` hook shape,
writes periodic train_loss/eval_loss/gpu_utilization_pct/vram_used_gb/tokens_per_second
snapshots to Postgres instead of Redis — kept as a separate class so `MetricsCallback`
itself stays Redis-only per its own PHASE2-007 docstring), both sharing one
`GPUMonitor().sample` instance (called twice per fire — acceptable, pynvml calls are
sub-millisecond). DPO/ORPO preference-pair row validation is *not* duplicated at
dispatch time — deliberately left to each trainer's own `prepare_preference_rows()` to
raise `TrainerError`, caught in `run_training_job`'s try/except and reported as a
normal job failure with that exact error message.

Added `psycopg2-binary==2.9.9` to `training_engine/requirements.txt` (training_engine
had zero Postgres driver before this — `minio==7.2.7` was already pinned but unused
until now, confirming the original docker-compose.gpu.yml author's intent that
training_engine talk to MinIO directly). Added `postgres` to docker-compose.gpu.yml's
`training_engine` service `depends_on` (it previously only depended on redis+minio,
since it had no DB-writing responsibility before this task). Added
`TRAINING_OUTPUT_DIR` to `.env.example` (defaults to `/training_engine/output` if
unset, mirroring every other training_engine env-var-with-fallback pattern).

**Known limitation, not addressed this session:** dataset rows are downloaded and
parsed entirely in training_engine's own process (never sent through the Celery
broker — the backend's dispatch task only passes the small `dataset_storage_path`/
`dataset_format` strings, not materialized rows), which avoids large Celery message
payloads for big datasets. This was a deliberate design choice during implementation,
not something the user was asked about directly — flag if it ever needs revisiting.

40 new tests across both processes — `apps/backend`: 96/96 passing (5 new:
`test_training_tasks.py` covering rlhf rejection, no-dataset rejection, happy-path
queued+send_task, dataset_format defaulting, connection-closed-on-early-return; plus 2
new dispatch-wiring tests in `test_job_routes.py`). `training_engine`: 103/103 passing
(21 new: `test_job_status.py` for the DB helpers + `MetricsPersistCallback`,
`test_storage.py` for the MinIO download helper, `test_tasks.py` for
`run_training_job`'s dispatch/error/happy-path branches). Hit the standing "PostToolUse
hook strips a freshly-added unused import between separate Edit calls" gotcha three
times in this session (job_service.py's `dispatch_training_job` import,
test_job_routes.py's `job_service` import, test_storage.py's `contextlib` import) —
recovered each time by re-adding the import once its usage already existed in the file.
Also hit the standing "bare `cd dir && cmd` leaks Bash cwd forward" gotcha once (broke
the lint hook's relative path resolution for the next Edit) — recovered with a plain
`cd` back to repo root; all later shell commands used `(cd dir && cmd)` subshell syntax.
Local pytest runs needed the real `.env` password (`fts_dev_password_2024`), not
`.env.example`'s placeholder (`fts_password_change_in_production`) — first full backend
run failed everything with `InvalidPasswordError` until corrected.

Pushed `feat/PHASE2-009-celery-training-task`; PR not opened (manual creation per
established workflow).
