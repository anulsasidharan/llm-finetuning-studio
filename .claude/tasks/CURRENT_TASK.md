# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-010
## TASK NAME: Frontend — login + register pages with Zod validation
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-010-auth-pages

## OBJECTIVE
Per CLAUDE.md section 2 (`app/(auth)/login/page.tsx`, `app/(auth)/register/page.tsx`,
`app/(auth)/layout.tsx`) and section 6's TS conventions (RHF + Zod for forms):
build the actual login and register pages that consume PHASE1-WEEK3-009's
`useAuth` hook. This is the first page either route group has had — the
`(auth)` route group directory doesn't exist yet.

## ACCEPTANCE CRITERIA (DRAFT — confirm against useAuth/backend before starting)
- [ ] `app/(auth)/layout.tsx` — minimal layout for unauthenticated pages (no
      Sidebar/Header from the dashboard shell)
- [ ] `app/(auth)/login/page.tsx` — email + password form, React Hook Form +
      Zod schema, calls `useAuth().login`, redirects to `/` on success, shows
      a real error message on 401 (backend's `UnauthorizedError` detail)
- [ ] `app/(auth)/register/page.tsx` — email + password + full_name form,
      Zod schema mirroring backend's `UserRegister` (`password` min_length=8),
      calls `useAuth().register`, then — decide: auto-login after register
      (chain a `login` call with the same credentials, since `/register`
      itself returns no tokens) vs. redirect to `/login` with a "registered,
      please sign in" message. Real fork, not in useAuth's original scope —
      confirm with the user.
- [ ] Decide redirect target after login: dashboard home (`/`) vs. wherever
      the user was trying to go (no "redirect back to intended page" logic
      exists yet — confirm whether that's in scope now or deferred)
- [ ] Wire actual navigation: once `/login` exists, double check
      `lib/api.ts`'s 401-refresh-failure redirect (`window.location.href =
      "/login"`, added PHASE1-WEEK3-009) actually lands somewhere real
- [ ] `apps/frontend` lints/builds clean (`npm run lint`, `npm run build`)
- [ ] Manually verify the real login/register flow now that a page exists —
      this task is the first one that CAN use an actual page render, unlike
      PHASE1-WEEK3-009 which had no page to test against. If no browser tool
      is available (confirmed absent as of PHASE1-WEEK3-009 — see MEMORY.md),
      fall back to the documented Node-script-against-the-real-module
      technique, or note explicitly what could not be verified.

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-010-auth-pages
```

### Step 2 — Confirm scope with the user before writing code
Resolve the two flagged forks above: (1) auto-login after register vs.
redirect-to-login-with-message, (2) whether "redirect back to intended page"
is in scope for this task or deferred.

### Step 3 — Implement layout + both pages + Zod schemas

### Step 4 — Verify
`npm run lint` / `npm run build`. Exercise the actual rendered pages this
time (first task that can). Note in the session log exactly how this was
done.

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK3-010
3. BACKLOG.md → PHASE1-WEEK3-010 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with next Week 3 task (PHASE1-WEEK3-011:
   Dataset Studio page — upload + format + quality report)

## BLOCKERS
None yet identified — the two scope questions above need confirmation with
the user before coding starts, same pattern as recent tasks.

## NOTES FOR NEXT TASK

**`hooks/useAuth.ts` (PHASE1-WEEK3-009) is done.** `useAuth()` returns
`{ user, isLoadingUser, isAuthenticated, login, isLoggingIn, loginError,
register, isRegistering, registerError, logout }`. `login`/`register` are
`mutateAsync` functions (throw on failure, so wrap in try/catch or check
`loginError`/`registerError` from the hook). `login` takes
`{ email, password }`; `register` takes `{ email, password, full_name }`
matching backend's `UserRegister` exactly — note `register` does NOT log
the user in (the backend endpoint returns `UserResponse`, not tokens), so
this task must decide what happens right after a successful register.

**Refresh token storage + 401 handling decided in PHASE1-WEEK3-009:**
refresh token lives in `localStorage` under `fts_refresh_token` (NOT an
httpOnly cookie — deviates from ARCHITECTURE.md's diagram, see MEMORY.md's
ARCHITECTURE DECISIONS for why). `lib/api.ts`'s response interceptor does
silent refresh-and-retry on 401 and falls back to
`window.location.href = "/login"` on refresh failure — **this task is what
makes that redirect actually land somewhere**, since `/login` doesn't exist
until now.

**`app/providers.tsx` (`QueryClientProvider`) now wraps the whole app**
(wired into `app/layout.tsx` in PHASE1-WEEK3-009) — any `useQuery`/
`useMutation` in this task's pages will work without additional setup.

**No browser-automation tool is available in this environment** (confirmed
via `ToolSearch` during PHASE1-WEEK3-009). PHASE1-WEEK3-009 verified
client-only logic via direct backend `curl` calls plus a temporary
`node --experimental-strip-types` script (written, run, deleted before
committing) that imported the real module with a minimal `window`/
`localStorage` shim. This task is the first that produces an actual
rendered page — fetching the page's initial server-rendered HTML over HTTP
(the technique used successfully in PHASE1-WEEK3-006) will show the static
form markup, but exercising the interactive submit→login→redirect flow
will likely need the same temporary-script fallback unless a browser tool
becomes available. Say explicitly what was/wasn't verified.

**Gotcha, repeated across many sessions:** the PostToolUse hook
(`.claude/hooks/lint.py`) resolves paths relative to the Bash tool's
current working directory — a bare `cd apps/frontend && cmd` (no subshell
parens) leaks the cwd forward and breaks the hook on the next Edit/Write,
and also breaks relative-path shell commands (`rm`, `git status` showing
unexpectedly short paths) run afterward in the same session. Confirmed yet
again during PHASE1-WEEK3-009. Always wrap `cd`-then-run in
`(cd dir && cmd)`, or `cd` straight back to repo root immediately after a
bare `cd`.

**Gotcha, backend-specific:** the PostToolUse lint/format hook auto-fixes
"unused" imports between separate `Edit` calls on backend Python files —
always add an import and its first usage in the same `Edit`/`Write` call.

**LANDMINE, still unresolved (not relevant unless a future task touches
`training_engine/datasets/loader.py`):** `training_engine/datasets/`
collides by name with the pip-installed `datasets==2.19.0` (HuggingFace)
library in `training_engine/requirements.txt`. Resolve before any future
`loader.py` work.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-009)
Completed 2026-06-19. User confirmed two scope questions before coding: (1)
refresh-token storage — localStorage (`fts_refresh_token`) over
ARCHITECTURE.md's httpOnly-cookie diagram, since the backend's `/auth/refresh`
takes the token in the JSON body with no cookie code anywhere; (2) 401
handling — silent refresh-and-retry over a bare redirect. Built
`hooks/useAuth.ts` (TanStack Query wrapping login/register/logout/me),
rewrote `lib/api.ts`'s response interceptor with a single-flight
refresh-and-retry, added `app/providers.tsx` (`QueryClientProvider`, first
real wiring of `@tanstack/react-query`), and extracted `Header`'s account
dropdown into a new `AccountMenu` client component wired to real user data
+ working sign-out. Verified via lint/build (clean), direct backend `curl`
calls confirming the live API contract, and a temporary
`node --experimental-strip-types` script (deleted before committing) that
exercised the real interceptor code end-to-end against the live backend,
proving the corrupted-access-token → silent-refresh → transparent-retry path
genuinely works. No browser-automation tool is available in this
environment — noted explicitly rather than claimed. Pushed
`feat/PHASE1-WEEK3-009-use-auth`; PR not opened (manual creation per
established workflow).
