# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-006
## TASK NAME: Frontend — Next.js root layout + sidebar + header
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-006-frontend-layout

## OBJECTIVE
Per CLAUDE.md section 2 directory structure / Week 3 checklist: build the
dashboard shell that every later frontend page (datasets, methodology,
config, training, evaluation, experiments, models, deploy) will render
inside. `apps/frontend` currently only has the Next.js 14 default
`app/layout.tsx` + `app/page.tsx` and a `components/ui/` (shadcn) set —
no `(auth)`/`(dashboard)` route groups, no `components/layout/` exist
yet. This task creates the dashboard route group's layout, sidebar, and
header; it does NOT build auth pages, the dataset/methodology/etc. pages
themselves, or wire real API calls (those are later Week 3/Phase 2
tasks).

## ACCEPTANCE CRITERIA (DRAFT — confirm against CLAUDE.md before starting)
- [ ] `app/(dashboard)/layout.tsx` — wraps children with `Sidebar` +
      `Header`, per CLAUDE.md section 2's directory tree
- [ ] `app/(dashboard)/page.tsx` — minimal dashboard home placeholder
      (real content is a later task)
- [ ] `components/layout/Sidebar.tsx` — nav links for all module routes
      listed in CLAUDE.md section 2 (onboarding, datasets, methodology,
      config, gpu-selector, cost-estimator, training, evaluation,
      experiments, models, deploy)
- [ ] `components/layout/Header.tsx` — placeholder user/account area
      (no real auth wiring yet — `useAuth` hook lands in
      PHASE1-WEEK3-009)
- [ ] `components/layout/Breadcrumb.tsx` + `components/layout/
      PageContainer.tsx` — also named in CLAUDE.md section 2's
      `layout/` directory; confirm with the user whether to build both
      now or defer `Breadcrumb` until a page actually needs it (real
      scope question — CLAUDE.md lists the file but no task has used it
      yet)
- [ ] Server vs Client: layout/page stay RSC by default; mark only the
      interactive parts (e.g. a collapsible sidebar toggle, if any)
      `"use client"`, per CLAUDE.md's coding conventions
- [ ] Tailwind utilities only — no inline styles, per CLAUDE.md
- [ ] `apps/frontend` lints/builds clean (`npm run lint`, `npm run
      build` or equivalent — confirm exact scripts in
      `apps/frontend/package.json` before running)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-006-frontend-layout
```

### Step 2 — Confirm scope with the user before writing code
Resolve the `Breadcrumb`/`PageContainer` now-vs-defer question above,
and confirm the sidebar's exact nav item list/icons/grouping if CLAUDE.md
section 2 leaves any ambiguity.

### Step 3 — Implement layout + components

### Step 4 — Verify
Check `apps/frontend/package.json` for the actual lint/build script
names first (don't assume `npm run lint`/`npm run build` exist verbatim).
Manually sanity-check the rendered shell via the dev server if feasible
in this environment.

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK3-006
3. BACKLOG.md → PHASE1-WEEK3-006 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with next Week 3 task (PHASE1-WEEK3-007:
   frontend lib/api.ts typed axios client)

## BLOCKERS
None yet identified — the Breadcrumb/PageContainer now-vs-defer question
above needs a quick scope confirmation with the user before coding
starts, same pattern as recent backend tasks.

## NOTES FOR NEXT TASK
**Backend Week 3 scope (PHASE1-WEEK3-001 through 005) is fully closed.**
All remaining Week 3 tasks (006–013) are frontend-only and don't touch
`apps/backend`.

Still open from PHASE1-WEEK2-009 (optional, low priority): `core/auth.py`'s
local `CREDENTIALS_EXCEPTION = HTTPException(401)` could be migrated to
the `core/exceptions.py` `UnauthorizedError` hierarchy now that both the
hierarchy and its FastAPI exception handler exist — not a hard
requirement, just consistency cleanup.

Known unrelated issue (not in scope, just flagged): `fts_backend`'s
Docker `start.sh` fails with `set: Illegal option -` on container start
in this environment — looks like a CRLF line-ending issue from a Windows
checkout corrupting a `set -euo pipefail` (or similar) line. Verification
has been worked around by running the app locally via `uv run uvicorn`
against host-mapped ports instead of inside the `fts_backend` container.
Worth a dedicated fix-it task at some point.

**Gotcha, repeated across multiple sessions:** the PostToolUse lint/format
hook auto-fixes "unused" imports between separate `Edit` calls on backend
Python files — adding an import in one `Edit` and its only usage in a
later, separate `Edit` lets the hook strip the import in between. Always
add an import and its first usage in the same `Edit`/`Write` call. (Not
yet confirmed whether an equivalent ESLint-on-save hook exists for the
frontend — check `.claude/hooks/` before assuming it doesn't.)

**LANDMINE, still unresolved (not relevant unless a future task touches
`training_engine/datasets/loader.py`):** `training_engine/datasets/`
collides by name with the pip-installed `datasets==2.19.0` (HuggingFace)
library in `training_engine/requirements.txt`. Resolve before any future
`loader.py` work.

**Standing architectural pattern (PHASE1-WEEK3-004):** when a backend
route needs logic that lives in `training_engine` (a separate standalone
process/environment from `apps/backend`), port the logic into
`apps/backend/services/` as a near-verbatim copy rather than installing
`training_engine` as a backend dependency or dispatching via Celery. Not
relevant to this frontend task, but keep in mind for any future backend
work this session might also touch.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-005)
Completed 2026-06-19. User chose minimal per-method required keys for
training_config validation (over generic-only or strict full schema).
Added `schemas/job.py` (`FineTuneJobCreate`/`FineTuneJobResponse`/
`FineTuneJobConfigResponse`), `services/job_service.py`
(`SUPPORTED_METHODOLOGIES`, `COMMON_REQUIRED_KEYS` +
`METHOD_SPECIFIC_REQUIRED_KEYS` per methodology, `create_job` reusing
`dataset_service.get_dataset` for `dataset_id` ownership checks,
`list_jobs`/`get_job`), `api/v1/routes/jobs.py` (`POST /jobs`,
`GET /jobs`, `GET /jobs/{id}`, `GET /jobs/{id}/config`, all
`Depends(get_current_user)`). 16 new tests in `tests/test_job_routes.py`.
Full suite 80/80 passing, ruff clean. Pushed
`feat/PHASE1-WEEK3-005-job-creation`; PR not opened (manual creation per
established workflow).
