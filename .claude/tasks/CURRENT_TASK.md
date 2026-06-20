# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-012
## TASK NAME: Frontend — Training Config Builder skeleton
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-012-config-builder

## OBJECTIVE
Per CLAUDE.md section 2 (`app/(dashboard)/config/page.tsx`, `app/(dashboard)/config/[jobId]/page.tsx`,
`components/training/ConfigBuilder.tsx`, `ParameterField.tsx`, `MethodologyCard.tsx`,
`JobStatusBadge.tsx`, `TrainingControls.tsx`) and BACKLOG.md's description ("all
sections rendered"): build the skeleton for the Training Config Builder — the
page(s) and components that will eventually let a user pick a methodology, fill
in training parameters, and create a `FineTuneJob` via `POST /jobs`
(`apps/backend/api/v1/routes/jobs.py`, built PHASE1-WEEK3-005). This is a
**skeleton** task — full per-parameter validation/education is PHASE1-WEEK3-013
(`ParameterTooltip`) and beyond; confirm with the user how much real
functionality (e.g. actually wiring `POST /jobs`) belongs in this task vs. later
ones before assuming scope.

## KNOWN GAPS TO CONFIRM WITH THE USER BEFORE CODING
- `FineTuneJobCreate` (backend) requires `base_model_id` — there is no
  `GET /models/catalog` route yet (CLAUDE.md lists it, but check
  `apps/backend/api/v1/routes/` before assuming it exists; `model_catalog`
  table + seed data exist since PHASE1-WEEK2-013, but the route itself may not).
  If missing, decide: stub the model picker, add the missing route, or scope
  this task to not need it yet.
- `training_config` is a free-form dict on the backend, validated only by
  `job_service.COMMON_REQUIRED_KEYS`/`METHOD_SPECIFIC_REQUIRED_KEYS` per
  methodology (see MEMORY.md ARCHITECTURE DECISIONS / PHASE1-WEEK3-005) — decide
  how literally the "full parameter panel" from CLAUDE.md section 1 should be
  built now vs. deferred.
- Confirm whether this task should actually call `POST /jobs` end-to-end, or
  stay a pure UI skeleton (no submission wired yet) — BACKLOG.md's phrase "all
  sections rendered" suggests the latter, but don't assume.

## ACCEPTANCE CRITERIA (DRAFT — confirm scope against the gaps above first)
- [ ] `components/training/MethodologyCard.tsx` — displays one methodology
      (sft/lora/qlora/dpo/orpo/rlhf) with its key differentiator, VRAM usage,
      min samples (CLAUDE.md section 7 table)
- [ ] `components/training/ConfigBuilder.tsx` — renders all config sections
      (methodology selection + parameter groups), skeleton-level (real
      submission may be deferred per scope confirmation above)
- [ ] `components/training/ParameterField.tsx` — generic labeled input wrapper
      for one training parameter (no tooltip yet — that's PHASE1-WEEK3-013)
- [ ] `components/training/JobStatusBadge.tsx` — badge for `FineTuneJobStatus`
      (pending/queued/running/completed/failed/cancelled)
- [ ] `components/training/TrainingControls.tsx` — start/pause/cancel button
      group (skeleton — no live job to control yet, Phase 2 wires real actions)
- [ ] `app/(dashboard)/config/page.tsx` — hosts `ConfigBuilder`
- [ ] `app/(dashboard)/config/[jobId]/page.tsx` — placeholder detail/edit view
- [ ] `apps/frontend` lints/builds clean (`npm run lint`, `npm run build`)
- [ ] Verify against a locally running backend wherever this task does call a
      real endpoint; state explicitly which parts are skeleton-only vs.
      live-wired

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-012-config-builder
```

### Step 2 — Confirm scope with the user
Resolve the gaps listed above before writing code.

### Step 3 — Implement components + pages

### Step 4 — Verify
`npm run lint` / `npm run build`. Exercise any real backend calls this task
makes against a locally running backend; note in the session log exactly what
was verified live vs. left as skeleton.

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK3-012
3. BACKLOG.md → PHASE1-WEEK3-012 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with next Week 3 task (PHASE1-WEEK3-013:
   ParameterTooltip component)

## BLOCKERS
None yet identified — the model-catalog-route and submission-scope gaps (see
KNOWN GAPS above) need confirmation with the user before coding, same pattern
as recent tasks.

## NOTES FOR NEXT TASK

**Dataset Studio (PHASE1-WEEK3-011) is done.** `app/(dashboard)/datasets/`
(list, upload, `[datasetId]` detail) and `components/dataset/*` exist and work
end-to-end against the real backend, including a newly added
`GET /datasets/{id}` route. `GET /datasets/{id}/preview` and
`DatasetPreview.tsx` were explicitly skipped (no backend route) and are an
open backend follow-up, not yet scheduled in BACKLOG.md — flag this if a
future task's scope brushes against dataset previews.

**This codebase's shadcn/ui setup uses base-ui's `render` prop, not the
conventional shadcn `asChild` prop.** To make `Button`/`Badge`/etc. render as a
different element (e.g. a `<Link>`), write
`<Button render={<Link href="..." />}>label</Button>`, not
`<Button asChild><Link>...</Link></Button>`. See `components/ui/dialog.tsx`'s
existing `<DialogPrimitive.Close render={<Button variant="outline" />}>` for
the established example. This will matter for `TrainingControls.tsx` if any
of its buttons need to be links.

**`hooks/useDatasets.ts` is the second hook built following `useAuth.ts`'s
pattern** (request functions colocated with `useQuery`/`useMutation` wrappers,
cache invalidation on mutation success). If this task wires `POST /jobs` for
real, follow the same pattern in a new `hooks/useJobs.ts` rather than inventing
a different shape.

**No browser-automation tool is available in this environment** (confirmed
repeatedly through PHASE1-WEEK3-009/010/011). Established fallback: fetch
server-rendered HTML over `curl` for static markup, `curl` the real backend
directly to confirm live API contracts, and — for genuinely interactive/
client-only logic — a temporary `node --experimental-strip-types` script
(written, run, then deleted before committing) importing the real module
(e.g. `lib/api.ts` or a hook's request functions) with a minimal
`window`/`localStorage` shim to exercise the actual shipped code end-to-end.

**Gotcha, repeated across many sessions:** the PostToolUse hook
(`.claude/hooks/lint.py`) resolves paths relative to the Bash tool's current
working directory — a bare `cd apps/frontend && cmd` (no subshell parens)
leaks the cwd forward and breaks the hook on the next Edit/Write. Always wrap
`cd`-then-run in `(cd dir && cmd)`, or `cd` straight back to repo root
immediately after a bare `cd`. Confirmed yet again during PHASE1-WEEK3-011.

**Gotcha, environment-specific:** Docker containers (`fts_postgres`,
`fts_redis`, `fts_minio`, etc.) are NOT running by default between sessions —
check `docker ps -a` before assuming they're up, bring up only what's needed,
and stop them again at the end of the session. When running the backend
locally outside Docker, the `.env` defaults point at Docker-internal
hostnames/ports and need overriding: `DATABASE_URL`/`DATABASE_URL_SYNC` →
`localhost:5433`; `REDIS_URL` → `redis://:fts_redis_dev_2024@localhost:6380/0`
(password required even though the in-Docker default doesn't need an explicit
one set locally); MinIO needs **`MINIO_HOST=localhost` + `MINIO_PORT=9000`**
specifically (not `MINIO_ENDPOINT`, which `core/storage.py` never actually
reads). Also check for stale `uv run uvicorn` processes still holding port
8000 from earlier attempts in the same session before assuming a fresh
`nohup ... &` actually took effect — confirmed this bit PHASE1-WEEK3-011.

**Gotcha, backend-specific:** the PostToolUse lint/format hook auto-fixes
"unused" imports between separate `Edit` calls on backend Python files —
always add an import and its first usage in the same `Edit`/`Write` call.

**LANDMINE, still unresolved (not relevant unless a future task touches
`training_engine/datasets/loader.py`):** `training_engine/datasets/`
collides by name with the pip-installed `datasets==2.19.0` (HuggingFace)
library. Resolve before any future `loader.py` work.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-011)
Completed 2026-06-19. User confirmed one scope question before coding: add
`GET /datasets/{id}` (the service function already existed, just unexposed)
and skip `GET /datasets/{id}/preview`/`DatasetPreview.tsx` entirely as a
flagged backend follow-up, rather than build either preview path. Built the
full Dataset Studio: list page (table + empty state), upload page
(`DatasetUploader` with client-side extension validation), and a detail page
wiring `FormatSelector` (detect/re-detect format) and `QualityReport` (renders
the persisted quality_report JSON) plus a quality-check trigger — all backed
by a new `hooks/useDatasets.ts` following the `useAuth.ts` pattern. Extracted
`getErrorDetail` into `lib/utils.ts` as a shared helper. Discovered this
codebase's shadcn setup uses base-ui's `render` prop instead of `asChild`,
caught and fixed two `asChild`-style usages before they'd have type-errored.
Verified: backend full suite 84/84 passing; frontend lint/build clean (two
real type errors fixed along the way); full live upload→format→quality-check→
get→list flow curl'd end-to-end against a locally running backend; all three
new routes' server-rendered HTML fetched and confirmed to mount without
crashing; a temporary Node script (deleted before committing) drove the real
`lib/api.ts` axios instance through the entire flow with real assertions
against the live backend. Cleaned up verification test users and restored all
Docker containers/dev processes to their pre-session state. Pushed
`feat/PHASE1-WEEK3-011-dataset-studio`; PR not opened (manual creation per
established workflow).
