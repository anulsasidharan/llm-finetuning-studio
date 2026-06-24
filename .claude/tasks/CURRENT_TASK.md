# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE2-014
## TASK NAME: Frontend GPU Selector page
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 2, Week 4
## BRANCH: feat/PHASE2-014-gpu-selector (not yet cut)

## OBJECTIVE
Per BACKLOG.md and CLAUDE.md's Core Capabilities list — build the
Multi-cloud GPU Selector: compare and launch across AWS, GCP, Azure, RunPod,
Lambda Labs.

## CONTEXT FROM PRIOR SESSIONS
- **Unlike PHASE2-013 (pure frontend), this task needs real backend work
  first** — confirmed no `GET /gpu/instances`, `GET /gpu/pricing`, or
  `POST /gpu/estimate` route exists yet (`apps/backend/api/v1/routes/` only
  has `auth.py`, `datasets.py`, `experiments.py`, `jobs.py`, `models.py` — no
  `gpu.py`). This mirrors PHASE2-012's "built ground-up" shape, not
  PHASE2-013's "data/component already existed" shape.
- `apps/backend/models/gpu_pricing.py` (ORM model) already exists, and the
  `gpu_pricing` table was already created + seeded by
  `apps/backend/scripts/seed_data.py` back in PHASE1-WEEK2-013 — confirmed
  via the Alembic migration `5d716f49b7ac_add_model_catalog_and_gpu_pricing_tables.py`.
  Check that model's actual columns before designing
  `schemas/gpu.py`/`services/gpu_service.py` — don't assume shape from
  CLAUDE.md's route table alone.
- `apps/frontend/components/gpu/` and `apps/frontend/app/(dashboard)/gpu-selector/`
  are both **empty directories** (no files at all yet) — same
  "sidebar/scaffold built ahead of pages" pattern as `methodology/` was
  before PHASE2-013; not a sign anything is half-built. Sidebar already
  links to `/gpu-selector` (`components/layout/Sidebar.tsx`).
- CLAUDE.md's section 9 lists real RunPod/Lambda Labs API doc links — but
  PHASE3-001 ("GPU pricing service — RunPod + Lambda Labs API integration")
  is a *separate*, later backlog item. Don't scope-creep into live cloud API
  calls here; PHASE2-014 should read from the already-seeded `gpu_pricing`
  table, same as `models.py`'s catalog routes read from `model_catalog`.
- Generated frontend types (`types/api-schema.d.ts`/`types/index.ts`) won't
  have GPU response shapes until the backend schema exists and
  `scripts/export_openapi.py` + `npm run generate:types` are rerun — same
  codegen pipeline already used for every other resource (see
  PHASE1-WEEK3-008's memory entry).
- No browser-automation tool is available in this environment (confirmed
  repeatedly across PHASE2-010/011/012/013) — expect the same verification
  fallback: `npm run lint`/`npm run build`, curl against a local backend, and
  the SSR-HTML-check fallback for anything client-interaction-only.

## PREVIOUS TASK SUMMARY (PHASE2-013)
Completed 2026-06-24. The task's flagged open design question (what drives
"auto-recommendation") was resolved via `AskUserQuestion` before writing any
code: the user chose **"short questionnaire only"** — a small client-side
form (goal: plain task vs. preference alignment; VRAM budget: low/medium/
high; approx. dataset row/pair count) with no dependency on already-uploaded
datasets via `useDatasets`.

Built: `apps/frontend/lib/methodology-recommendation.ts` — pure
`recommendMethodology({goal, vramBudget, datasetRows})` function (no React,
fully unit-testable in principle) returning `{methodology, belowMinSamples}`.
Rule: `alignment` goal maps to RLHF (only if `vramBudget==="high"` AND rows
>= 10,000) / DPO (medium-or-high VRAM) / ORPO (low VRAM); `plain_task` goal
maps to SFT (high VRAM) / LoRA (medium) / QLoRA (low). Keeps its own
`MIN_SAMPLES: Record<Methodology, number>` map as plain numbers, deliberately
separate from `lib/methodology-data.ts`'s display-string `minSamples` field
(CURRENT_TASK.md's prior note said don't duplicate that file — this is a
parallel derived concern, not a duplicate of the display copy).

`components/training/MethodologyCard.tsx` got one additive change: a new
optional `recommended?: boolean` prop rendering a second "Recommended"
(`variant="secondary"`) badge alongside the existing "Selected" badge — reused
as-is otherwise, both in `ConfigBuilder.tsx` (always `recommended={false}`,
unchanged behavior) and the new wizard.

New `components/training/MethodologyRecommender.tsx` (`"use client"`): the
questionnaire (Select x2 + Input) feeds `recommendMethodology` reactively via
`useMemo`; an `Alert` banner shows the live recommendation with a "Use
recommended" button; a destructive `Alert` appears only when
`belowMinSamples` is true; the full `METHODOLOGY_INFO` grid renders below
with independent click-to-select state (`selected`, initialized from the
recommendation at mount, then fully user-controlled — does not silently
snap back when the questionnaire changes, only the "Recommended" badge and
banner move). A "Continue to training config" button does
`router.push(\`/config?methodology=${selected}\`)`.

New `app/(dashboard)/methodology/page.tsx` — same `PageContainer` + heading
pattern as every other dashboard page, no longer an empty directory.

Closed the loop into the existing Config Builder: `ConfigBuilder.tsx` now
reads `useSearchParams().get("methodology")` to seed `useForm`'s
`defaultValues.methodology` (validated against the existing
`METHODOLOGY_VALUES` tuple, falling back to the prior hardcoded `"lora"`
default if absent/invalid) — this is the **first** `useSearchParams` call in
this codebase outside the `(auth)` route group's login/register pages. Per
Next.js 16's prerendering rules (confirmed via
`node_modules/next/dist/docs/.../use-search-params.md`, same as
`(auth)/login/page.tsx` already does), a static page calling
`useSearchParams` from a Client Component must be wrapped in `<Suspense>` or
the production build fails — added `<Suspense fallback={null}>` around
`<ConfigBuilder />` in `app/(dashboard)/config/page.tsx` to match.

Verified via `npm run build` (clean; `/methodology` and `/config` both still
prerender as static `○` routes) and the established SSR-HTML-grep fallback
(no browser tool in this environment): confirmed the built
`.next/server/app/methodology.html` contains the questionnaire copy, the
recommendation banner, the CTA, and all six methodology labels
(SFT/LoRA/QLoRA/DPO/ORPO/RLHF), and that the default questionnaire state
(plain task + medium VRAM) recommends LoRA as designed. `npm run lint` is
clean (one pre-existing, unrelated React Compiler warning on
`ConfigBuilder.tsx`'s `watch()` call, present before this task). Not yet
committed/pushed — branch `feat/PHASE2-013-methodology-selector` was already
checked out at session start per the git status snapshot.
