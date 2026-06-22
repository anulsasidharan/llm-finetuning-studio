# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-012
## TASK NAME: Frontend Experiment Tracker UI
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-012-experiment-tracker (not yet cut)

## OBJECTIVE
Per BACKLOG.md and CLAUDE.md's Core Capabilities list — build the Experiment Tracker:
native versioning of runs, configs, metrics, and artifacts. CLAUDE.md section 5 lists
five routes for this (`GET/POST /experiments`, `GET /experiments/{id}`,
`POST /experiments/{id}/runs`, `GET /experiments/{id}/compare`) — **none of them exist
yet**, unlike every other PHASE2-0xx frontend task so far, which had a backend already
built and waiting. This task is backend + frontend, ground-up.

## CONTEXT FROM PRIOR SESSIONS
- `apps/backend/models/experiment.py` already exists (built PHASE1-WEEK2-003) — two ORM
  classes: `Experiment` (`id`, `user_id` FK, `name`, `description`, timestamps, `runs`
  relationship) and `ExperimentRun` (`id`, `experiment_id` FK, `fine_tune_job_id` FK,
  `metrics` JSONB, `created_at`). Already registered in `models/__init__.py` and
  `migrations/env.py`'s explicit import list, and the initial Alembic migration already
  created both tables (confirmed via `psql \d` historically) — no new migration should be
  needed unless this task's design needs new columns.
- No `schemas/experiment.py`, `services/experiment_service.py`, or
  `api/v1/routes/experiments.py` exist — this task builds all three, following the exact
  established pattern from `jobs`/`datasets` (Pydantic schema with
  `ConfigDict(from_attributes=True)`, service functions scoped to `user_id`, routes behind
  `Depends(get_current_user)`, regenerate `openapi/schema.json`/`types/api-schema.d.ts`
  afterward).
- `apps/frontend/app/(dashboard)/experiments/` exists as an **empty directory** (no
  `page.tsx` inside) — the Sidebar (PHASE1-WEEK3-006) already links to `/experiments` the
  same way it pre-links to every other not-yet-built module route; this is the established
  "sidebar built ahead of pages" pattern in this repo, not a sign anything is half-built.
- `GET /experiments/{id}/compare`'s exact response shape is a genuine open design
  question — CLAUDE.md doesn't specify it, and there's no existing analogous "compare"
  endpoint elsewhere in the backend to copy. Needs a decision before backend coding:
  likely candidates are (a) a list of each run's `fine_tune_job` config + final metrics
  side by side, or (b) something more structured (e.g. per-metric arrays for charting).
  Flag this explicitly to the user — don't guess.
- `POST /experiments/{id}/runs` takes presumably `fine_tune_job_id` (+ optional metrics
  snapshot?) to attach an existing job to an experiment as a tracked run — confirm whether
  `metrics` should be populated at creation time (e.g. copied from the job's current
  `train_loss`/`eval_loss`/etc. columns) or left null until some later update call (no
  `PATCH /experiments/{id}/runs/{run_id}` exists in CLAUDE.md's route table, so if metrics
  need to be refreshed later, that's either a gap to flag or a sign runs are meant to be
  point-in-time snapshots taken once at creation).
- The completed PHASE2-011 (this session) added `apps/frontend/lib/websocket.ts` and
  `components/charts/{LossChart,GPUUtilChart,VRAMChart}.tsx` — if the compare view ends up
  wanting a loss-curve-style chart across multiple runs, these are the closest existing
  prior art (plain `recharts` `LineChart`, no shared chart abstraction in this repo yet).
- No browser-automation tool is available in this environment (confirmed repeatedly) —
  expect the same verification fallback as every prior frontend task: `npm run
  lint`/`npm run build`, real backend + `curl`, and a temporary Node/script-based check
  where it adds real signal, deleted before committing.
- **New gotcha from PHASE2-011, see MEMORY.md ARCHITECTURE DECISIONS:** if this task ever
  needs to manually verify anything over `WS /ws/training/{job_id}` again, use the
  `websockets` pip package (`uv run python` from `apps/backend`), not a Node-native
  `WebSocket` script — the latter gave a false negative this session.

## ACCEPTANCE CRITERIA (DRAFT)
- [ ] Confirm the two open design questions above (compare response shape, run-metrics
      snapshot timing) with the user before writing backend code
- [ ] `schemas/experiment.py`, `services/experiment_service.py`,
      `api/v1/routes/experiments.py` — all five CLAUDE.md routes, scoped to current user,
      404 on missing/not-owned, wired into `api_router`
- [ ] Regenerate `openapi/schema.json`/`types/api-schema.d.ts`, add experiment types to
      `types/index.ts`
- [ ] `hooks/useExperiments.ts` (list/get/create/compare queries + create-run mutation,
      mirrors `useJobs.ts`'s pattern)
- [ ] `app/(dashboard)/experiments/page.tsx` (list + create) and
      `app/(dashboard)/experiments/[experimentId]/page.tsx` (detail — runs list,
      attach-a-job-as-a-run action, compare view)
- [ ] New backend tests following the existing `test_job_routes.py`/
      `test_dataset_routes.py` pattern (insert/cleanup via real local Postgres, no mocking
      the DB layer)
- [ ] `npm run lint`/`npm run build` clean; backend test suite clean
- [ ] Live end-to-end verification against a real local backend (register, create a job,
      create an experiment, attach the job as a run, fetch compare)

## STEPS TO COMPLETE

### Step 1 — Resolve the two open design questions with the user before coding

### Step 2 — Cut feature branch from develop
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE2-012-experiment-tracker
```

### Step 3 — Backend: schemas + service + routes + tests, regenerate frontend types

### Step 4 — Frontend: hooks/useExperiments.ts + experiments pages

### Step 5 — Verify: backend test suite, `npm run lint`/`npm run build`, live curl-based
end-to-end check against a real local backend (register → create job → create experiment
→ attach run → compare)

### Step 6 — Stage, commit, push

### Step 7 — Update tracking files

## PREVIOUS TASK SUMMARY (PHASE2-011)
Completed 2026-06-22. Both of CURRENT_TASK.md's flagged "open decisions" (charting
library, route placement) turned out to already be settled by the existing repo —
`recharts` was already an installed-but-unused dependency, and `.claude/SKILLS.md`
already documented the exact `NEXT_PUBLIC_WS_URL`/`useTrainingWebSocket` pattern to
follow — so no user interruption was needed.

Built `apps/frontend/lib/websocket.ts`'s `useTrainingSocket(jobId, enabled)` hook (JWT-
as-query-param auth per PHASE2-010, exposes `connectionState`/`status`/`metrics[]`, caps
history at 500, never auto-reconnects); `components/charts/{LossChart,GPUUtilChart,
VRAMChart}.tsx` (plain `recharts` `LineChart`s); new route
`app/(dashboard)/training/[jobId]/page.tsx` (separate from the existing read-only
`config/[jobId]/page.tsx`) showing live status + stat cards + all three charts, closing
the socket once the job is in a terminal state.

Hit the new `react-hooks/set-state-in-effect` lint rule (flags any direct `setState` call
in an effect's synchronous body, even inside a guard clause) — fixed by relying on
`useState`'s initial value for the disabled case and wrapping the remaining two
synchronous sets in `queueMicrotask(...)`.

**Real finding during live verification (see MEMORY.md ARCHITECTURE DECISIONS):** a
Node-native `WebSocket` test script produced a false negative against
`WS /ws/training/{job_id}` (looked like the backend dropped the Redis subscription
within ~1–2s); re-verified with the `websockets` pip package (same method PHASE2-010
used) and both `metrics_update`/`status_change` payloads arrived correctly — the backend
hub is fine, the Node built-in client is the unreliable piece for manual verification.

`npm run lint`/`npm run build` clean. Cleaned up: reverted temporary debug logging in
`training_hub.py` (zero net diff), deleted all temp scripts/logs, deleted the
verification user+job via `docker exec fts_postgres psql`, stopped the local non-Docker
backend process, left the already-running `fts_postgres`/`fts_redis`/`fts_minio`
containers as they were. Pushed `feat/PHASE2-011-training-dashboard`; PR not opened
(manual creation per established workflow).
