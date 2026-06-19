# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-011
## TASK NAME: Frontend — Dataset Studio page (upload + format + quality report)
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-011-dataset-studio

## OBJECTIVE
Per CLAUDE.md section 2 (`app/(dashboard)/datasets/page.tsx`,
`app/(dashboard)/datasets/upload/page.tsx`, `app/(dashboard)/datasets/[datasetId]/page.tsx`,
`components/dataset/DatasetUploader.tsx`, `FormatSelector.tsx`, `QualityReport.tsx`,
`DatasetPreview.tsx`): build the Dataset Studio — list datasets, upload a new
one, trigger format detection + quality check, and view the resulting report.
This is the first page consuming the backend's dataset endpoints
(`POST /datasets/upload`, `GET /datasets`, `POST /datasets/{id}/format`,
`POST /datasets/{id}/quality-check`, `GET /datasets/{id}/preview` — note: a
`GET /datasets/{id}/preview` route is listed in CLAUDE.md section 5 but does
NOT exist in `apps/backend/api/v1/routes/datasets.py` yet, only
upload/list/format/quality-check do — confirm scope on this gap before
building `DatasetPreview.tsx`).

## ACCEPTANCE CRITERIA (DRAFT — confirm against the real backend before starting)
- [ ] `app/(dashboard)/datasets/page.tsx` — lists the current user's datasets
      (`GET /datasets`) with filename, format, row count, created date; empty
      state when none exist
- [ ] `app/(dashboard)/datasets/upload/page.tsx` + `components/dataset/DatasetUploader.tsx`
      — file picker (`.json`/`.jsonl`), calls `POST /datasets/upload`
      (multipart), redirects to the dataset detail page on success, surfaces
      backend validation errors (oversized file, wrong content-type)
- [ ] `app/(dashboard)/datasets/[datasetId]/page.tsx` — detail page: dataset
      metadata, a "Detect format" action (`POST /datasets/{id}/format`), a
      "Run quality check" action (`POST /datasets/{id}/quality-check`),
      `components/dataset/QualityReport.tsx` rendering the persisted
      `quality_report` JSON (`total_rows`, `duplicate_rows`, `word_count`,
      `languages`)
- [ ] `components/dataset/FormatSelector.tsx` — shows/confirms the detected
      `format` (alpaca/sharegpt/chatml/unknown)
- [ ] **Resolve the `GET /datasets/{id}/preview` gap above with the user
      before building `DatasetPreview.tsx`** — route doesn't exist in the
      backend yet; options are likely (a) skip preview for this task and flag
      a backend follow-up, or (b) add the missing backend route as part of
      this task. Don't guess — this is a real spec/implementation mismatch.
- [ ] `apps/frontend` lints/builds clean (`npm run lint`, `npm run build`)
- [ ] Verify the real upload → format → quality-check flow against a locally
      running backend (same pattern as PHASE1-WEEK3-009/010 — no browser tool
      available, fall back to fetching rendered HTML + curl + a temporary
      Node script against the real module if interactive verification is
      needed)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-011-dataset-studio
```

### Step 2 — Confirm scope with the user before writing code
Resolve the `GET /datasets/{id}/preview` mismatch flagged above. Check
whether any other CLAUDE.md-listed route/component for this task is missing
from the real backend before assuming it exists.

### Step 3 — Implement pages + components

### Step 4 — Verify
`npm run lint` / `npm run build`. Exercise the real flow against a locally
running backend. Note in the session log exactly how this was done.

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK3-011
3. BACKLOG.md → PHASE1-WEEK3-011 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with next Week 3 task (PHASE1-WEEK3-012:
   Training Config Builder skeleton)

## BLOCKERS
None yet identified — the `GET /datasets/{id}/preview` route gap (see
OBJECTIVE) needs confirmation with the user before `DatasetPreview.tsx` work
starts, same pattern as recent tasks.

## NOTES FOR NEXT TASK

**`app/(auth)/login` and `app/(auth)/register` (PHASE1-WEEK3-010) are done.**
Login/register pages exist and work end-to-end against the real backend;
`lib/api.ts`'s 401-refresh-failure redirect now carries a `?next=` param back
to whatever protected page the user was trying to reach. Any future
protected page that wants a "redirect here after login" experience already
gets it for free via the existing interceptor — no new wiring needed.

**Dataset backend endpoints that exist today** (`apps/backend/api/v1/routes/datasets.py`,
built PHASE1-WEEK3-001/004): `POST /datasets/upload`, `GET /datasets`,
`POST /datasets/{id}/format`, `POST /datasets/{id}/quality-check`. There is
**no** `GET /datasets/{id}` (single-dataset fetch) or `GET /datasets/{id}/preview`
route yet, despite both being implied by CLAUDE.md's directory structure /
route table. The detail page route
(`app/(dashboard)/datasets/[datasetId]/page.tsx`) will need *some* way to
fetch one dataset's current state (e.g. after running format/quality-check)
— check whether `GET /datasets` (list) is enough to refetch-and-filter
client-side, or whether a new single-dataset backend route is actually
needed. Flag this explicitly with the user rather than assuming.

**`types/index.ts`'s `DatasetResponse`** (PHASE1-WEEK3-008) is generated from
the live OpenAPI spec and already includes `format`, `quality_report` (typed
as `Record<string, unknown>`), `row_count`, etc. — use it as-is; don't
hand-roll a parallel type.

**No browser-automation tool is available in this environment** (confirmed
repeatedly through PHASE1-WEEK3-009/010). The established fallback: fetch
server-rendered HTML over `curl` for static markup, `curl` the real backend
directly to confirm live API contracts, and — only if a genuinely
interactive/client-only path needs proving — a temporary
`node --experimental-strip-types` script (written, run, then deleted before
committing) importing the real module with a minimal `window`/`localStorage`
shim.

**Gotcha, repeated across many sessions:** the PostToolUse hook
(`.claude/hooks/lint.py`) resolves paths relative to the Bash tool's current
working directory — a bare `cd apps/frontend && cmd` (no subshell parens)
leaks the cwd forward and breaks the hook on the next Edit/Write, and also
breaks relative-path shell commands run afterward in the same session.
Confirmed yet again during PHASE1-WEEK3-010 (a bare `cd ... && grep`).
Always wrap `cd`-then-run in `(cd dir && cmd)`, or `cd` straight back to repo
root immediately after a bare `cd`.

**Gotcha, environment-specific:** Docker containers (`fts_postgres`,
`fts_redis`, `fts_minio`, etc.) are NOT running by default in this dev
environment between sessions — check `docker ps -a` before assuming they're
up, bring up only what's needed (`docker compose up -d postgres redis minio`),
and stop them again at the end of the session to restore the pre-session
state (confirmed via `docker ps -a` both before and after).

**Gotcha, backend-specific:** the PostToolUse lint/format hook auto-fixes
"unused" imports between separate `Edit` calls on backend Python files —
always add an import and its first usage in the same `Edit`/`Write` call.

**LANDMINE, still unresolved (not relevant unless a future task touches
`training_engine/datasets/loader.py`):** `training_engine/datasets/`
collides by name with the pip-installed `datasets==2.19.0` (HuggingFace)
library in `training_engine/requirements.txt`. Resolve before any future
`loader.py` work.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-010)
Completed 2026-06-19. User confirmed two scope questions before coding: (1)
post-register flow — auto-login with the submitted credentials (register
returns no tokens) over redirect-to-login-with-a-message; (2) "redirect back
to the intended page" — build it now, not deferred. Built the `(auth)` route
group (`layout.tsx`, `login/page.tsx`, `register/page.tsx`) with RHF + Zod
forms matching backend constraints exactly (`password.min(8)` on register),
and extended `lib/api.ts`'s 401-refresh-failure redirect to carry a `?next=`
param back to the page the user was trying to reach. Verified via lint/build
(clean, both routes still static), fetching real server-rendered HTML,
direct backend `curl` calls confirming the register→login chain and 401
error-body shape, and a temporary `node --experimental-strip-types` script
(deleted before committing) proving the new `next`-param redirect logic
works end-to-end against the real `lib/api.ts` module. No browser-automation
tool is available in this environment — the interactive click-through
inside the React components themselves was not directly exercised; noted
explicitly. Pushed `feat/PHASE1-WEEK3-010-auth-pages`; PR not opened
(manual creation per established workflow).
