# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-008
## TASK NAME: Frontend — types/index.ts shared types
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-008-shared-types

## OBJECTIVE
Per CLAUDE.md section 2 (`apps/frontend/types/index.ts`): build the shared
TypeScript types every later frontend task (useAuth, Dataset Studio, Config
Builder, job pages, etc.) will import. These should mirror the backend's
Pydantic response schemas so the typed axios client (`lib/api.ts`, built in
PHASE1-WEEK3-007) and TanStack Query hooks have real types to work against
instead of `any`.

## ACCEPTANCE CRITERIA (DRAFT — confirm against CLAUDE.md / backend schemas before starting)
- [ ] `types/index.ts` — types mirroring every backend Pydantic response
      schema that exists today: `UserResponse`, `TokenResponse` (schemas/auth.py),
      `DatasetResponse` (schemas/dataset.py), `FineTuneJobResponse` +
      `FineTuneJobConfigResponse` (schemas/job.py)
- [ ] Decide and confirm with the user: hand-write these types now (manual
      sync risk with backend schemas) vs. generate them from the FastAPI
      OpenAPI schema (more setup, but stays in sync automatically) — real
      scope question, don't guess silently
- [ ] Cover the enum-like string fields with real fields, not bare `string`
      where the backend already constrains them — e.g. `FineTuneJob.status`,
      `methodology` (six values per CLAUDE.md section 7), dataset format
      (alpaca/sharegpt/chatml/unknown)
- [ ] `apps/frontend` lints/builds clean (`npm run lint`, `npm run build`)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-008-shared-types
```

### Step 2 — Confirm scope with the user before writing code
Resolve the hand-write-vs-generate-from-OpenAPI question above. Read the
actual backend schema files (`apps/backend/schemas/{auth,dataset,job}.py`)
and the ORM models backing them before drafting fields, so the TS types are
accurate, not guessed.

### Step 3 — Implement types/index.ts

### Step 4 — Verify
`npm run lint` / `npm run build`. No real page consumes these yet beyond
type-checking, so verification is build/lint-level.

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK3-008
3. BACKLOG.md → PHASE1-WEEK3-008 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with next Week 3 task (PHASE1-WEEK3-009:
   frontend hooks/useAuth.ts with token refresh)

## BLOCKERS
None yet identified — the hand-write-vs-generate scope question above needs
a quick confirmation with the user before coding starts, same pattern as
recent tasks.

## NOTES FOR NEXT TASK
**`lib/api.ts` (PHASE1-WEEK3-007) is done.** Base axios instance at
`apps/frontend/lib/api.ts`, `baseURL` from `NEXT_PUBLIC_API_URL`. Request
interceptor reads a JWT from `window.localStorage.getItem("fts_access_token")`
via `getAccessToken()` and attaches `Authorization: Bearer <token>` when
present. Response interceptor is a bare pass-through — no real 401 handling
yet. **`useAuth` (PHASE1-WEEK3-009) MUST write the access token to that exact
same `fts_access_token` localStorage key**, or the interceptor silently stops
attaching the header. No per-endpoint typed helper functions exist in
`lib/api.ts` yet (user chose base-instance-only scope) — add them per-feature
as each page lands, now that this task's shared types exist to type response
bodies against.

**Frontend dashboard shell (PHASE1-WEEK3-006) is done.** `app/(dashboard)/
layout.tsx` wraps every future module page in `Sidebar` + `Header`;
`components/layout/PageContainer.tsx` exists for page-level padding.
`Breadcrumb.tsx` was deliberately deferred — build it only when a real
page needs it, not preemptively.

**Real bug fixed in PHASE1-WEEK3-006, worth knowing about:** `app/
globals.css` was missing the shadcn neutral theme CSS variables
(`--border`, `--muted`, `--primary`, `--card`, etc.) even though
`components.json` declares `cssVariables: true` — every `ui/*` component
was unstyled until this task became the first real consumer and the gap
was fixed. If any `ui/*` component still looks unstyled in a later task,
check `globals.css`'s `:root` / `@theme inline` blocks before assuming a
new bug.

**`app/page.tsx` (the default create-next-app scaffold) was deleted** —
`/` is now owned by `app/(dashboard)/page.tsx`. Don't recreate a bare
`app/page.tsx`; it would conflict with the dashboard route group.

**Gotcha, repeated across multiple sessions, now confirmed to apply to
the frontend half too:** the PostToolUse hook (`.claude/hooks/lint.py`)
resolves paths relative to the Bash tool's current working directory —
a bare `cd apps/frontend && cmd` (no subshell parens) leaks the cwd
forward and breaks the hook on the next Edit/Write (it looks for
`.claude/hooks/lint.py` relative to the leaked path). Always wrap
`cd`-then-run in `(cd dir && cmd)`, or `cd` straight back to repo root
immediately after a bare `cd`.

**Gotcha, backend-specific, still relevant if this session also touches
`apps/backend`:** the PostToolUse lint/format hook auto-fixes "unused"
imports between separate `Edit` calls on backend Python files — adding
an import in one `Edit` and its only usage in a later, separate `Edit`
lets the hook strip the import in between. Always add an import and its
first usage in the same `Edit`/`Write` call. Not yet confirmed whether
ESLint's `--fix` (run by the same hook on `.ts`/`.tsx` files) has the
same failure mode — watch for it.

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

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-007)
Completed 2026-06-19. User confirmed two scope questions before coding: (1)
401 handling — no-op pass-through for now, real redirect/refresh deferred to
PHASE1-WEEK3-009's `useAuth`; (2) route coverage — base axios instance only,
no per-endpoint helpers yet. Built `apps/frontend/lib/api.ts`: axios instance
with `baseURL: process.env.NEXT_PUBLIC_API_URL`, `getAccessToken()` reading
`window.localStorage["fts_access_token"]` (SSR-guarded), request interceptor
attaching `Authorization: Bearer <token>`, pass-through response interceptor.
No page consumes it yet — verified via `npm run lint` (clean) and `npm run
build` (Turbopack, compiled successfully, TypeScript passing, `/` still the
only static route). Pushed `feat/PHASE1-WEEK3-007-api-client`; PR not opened
(manual creation per established workflow).
