# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-007
## TASK NAME: Frontend — lib/api.ts typed axios client
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-007-api-client

## OBJECTIVE
Per CLAUDE.md section 2 (`apps/frontend/lib/api.ts`) and section 6's
coding convention ("API calls: Typed axios client in `lib/api.ts` only"):
build the single shared axios instance every later frontend task (useAuth,
Dataset Studio, Config Builder, etc.) will call through. No page wires a
real request yet — this task only builds the client itself.

## ACCEPTANCE CRITERIA (DRAFT — confirm against CLAUDE.md before starting)
- [ ] `lib/api.ts` — axios instance with `baseURL` from an env var
      (`NEXT_PUBLIC_API_URL` or similar — check `.env.example` for the
      existing convention before inventing a new var name)
- [ ] Request interceptor attaching the JWT access token (storage
      mechanism TBD — `useAuth`/token storage itself doesn't land until
      PHASE1-WEEK3-009, so this task only needs a read-the-token hook
      point, not the storage implementation)
- [ ] Response interceptor / 401 handling strategy — confirm with the
      user whether to stub this now (no-op or simple redirect-to-login)
      or fully defer to PHASE1-WEEK3-009 (real scope question — don't
      guess silently)
- [ ] Typed per-endpoint helper functions matching CLAUDE.md section 5's
      route table, or a thinner approach (confirm scope: full typed
      client for every route now vs. base instance only, with endpoint
      helpers added per-feature as each page lands)
- [ ] `apps/frontend` lints/builds clean (`npm run lint`, `npm run build`)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-007-api-client
```

### Step 2 — Confirm scope with the user before writing code
Resolve the 401-handling and full-vs-thin-client questions above.

### Step 3 — Implement lib/api.ts

### Step 4 — Verify
`npm run lint` / `npm run build`. No real page consumes this yet, so
verification is build/lint-level, not a rendered-page check.

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK3-007
3. BACKLOG.md → PHASE1-WEEK3-007 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with next Week 3 task (PHASE1-WEEK3-008:
   frontend types/index.ts shared types)

## BLOCKERS
None yet identified — the 401-handling-strategy and full-vs-thin-client
scope questions above need a quick confirmation with the user before
coding starts, same pattern as recent tasks.

## NOTES FOR NEXT TASK
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

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-006)
Completed 2026-06-19. User chose to build `PageContainer` now and defer
`Breadcrumb`. Added `app/(dashboard)/layout.tsx` + `page.tsx`,
`components/layout/{Sidebar,Header,PageContainer}.tsx`. Sidebar covers
all 12 CLAUDE.md module routes with lucide icons and active-link state
via `usePathname`; Header has a placeholder account dropdown (no real
auth). Fixed a real pre-existing gap: `globals.css` was missing the
shadcn neutral theme CSS variables every `ui/*` component depends on —
added the full token set. Deleted the default `app/page.tsx` scaffold
since `app/(dashboard)/page.tsx` now owns `/`. Verified via a live
`npm run dev` fetch (markup + compiled CSS inspection), not just
build/lint. `npm run lint` and `npm run build` both clean. Pushed
`feat/PHASE1-WEEK3-006-frontend-layout`; PR not opened (manual creation
per established workflow).
