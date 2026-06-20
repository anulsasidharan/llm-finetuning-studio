# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK3-013
## TASK NAME: Frontend — ParameterTooltip component
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 3
## BRANCH: feat/PHASE1-WEEK3-013-parameter-tooltip

## OBJECTIVE
Per CLAUDE.md section 2 (`components/training/ParameterTooltip.tsx`) and section 1's
"Training Config Builder — full parameter panel with inline contextual education" — build
the tooltip/popover component that explains what each training parameter does (e.g.
learning rate, LoRA rank, beta), then wire it into `ParameterField` (built
PHASE1-WEEK3-012, currently has no tooltip slot) so the parameters rendered by
`ConfigBuilder.tsx` actually carry contextual education, not just a bare label.

## CONTEXT FROM PHASE1-WEEK3-012
- `components/training/ParameterField.tsx` is a generic `Label` + input + error wrapper
  with no tooltip/help affordance yet — this task adds that, likely as an optional prop
  (e.g. `description`/`tooltip`) rendered next to the label via the existing
  `components/ui/tooltip.tsx` (already scaffolded in Week 1, unused so far) or
  `components/ui/popover.tsx`.
- `ConfigBuilder.tsx` renders these `ParameterField`s today with no help text:
  `learning_rate`, `num_epochs`, `batch_size` (common, backend-enforced),
  `warmup_ratio`, `weight_decay`, `max_seq_length`, `gradient_accumulation_steps`
  (broader extras, not backend-enforced), `lora_r`/`lora_alpha` (LoRA/QLoRA),
  `beta` (DPO/ORPO), `reward_model_id` (RLHF). Each needs a short, accurate
  explanation — confirm with the user whether copy should live centrally (e.g. a
  `PARAMETER_INFO` map keyed by field name, similar to `MethodologyCard.tsx`'s
  `METHODOLOGY_INFO` pattern) or be passed inline per-field in `ConfigBuilder.tsx`.
- This codebase's shadcn/ui setup uses base-ui's `render` prop, not the conventional
  `asChild` — check `components/ui/tooltip.tsx`'s actual API shape before wiring it
  (verify props the same way `dialog.tsx`/`select.tsx` were checked in prior sessions,
  don't assume Radix-style conventions transfer).

## KNOWN GAPS TO CONFIRM WITH THE USER BEFORE CODING
- Tooltip vs. popover: CLAUDE.md names the component `ParameterTooltip`, but a
  multi-sentence education panel (per CLAUDE.md's "visual explainers for LoRA, QLoRA,
  SFT, DPO, ORPO, RLHF" framing) may read better as a `Popover` (click-to-open, more
  room) than a `Tooltip` (hover, usually terse). Decide before building.
- Scope of copy: just a one-line description per parameter, or richer (valid range,
  typical default, why it matters per methodology)? Decide before writing 10 entries.

## ACCEPTANCE CRITERIA (DRAFT — confirm scope against the gaps above first)
- [ ] `components/training/ParameterTooltip.tsx` — the tooltip/popover component itself
- [ ] `ParameterField.tsx` extended with an optional prop to render it next to the label
- [ ] `ConfigBuilder.tsx`'s existing parameter fields actually pass real copy through
      the new prop (not just plumbing with no content)
- [ ] `apps/frontend` lints/builds clean (`npm run lint`, `npm run build`)
- [ ] Verify the new component mounts without crashing (server-rendered HTML check,
      per the standing no-browser-tool limitation) — note explicitly that the actual
      hover/click interaction can't be click-tested in this environment

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK3-013-parameter-tooltip
```

### Step 2 — Confirm scope with the user
Resolve the gaps listed above before writing code.

### Step 3 — Implement component + wire into ParameterField/ConfigBuilder

### Step 4 — Verify
`npm run lint` / `npm run build`. Fetch `/config` server-rendered HTML to confirm the
new markup mounts without crashing.

### Step 5 — Stage, commit, push

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK3-013
3. BACKLOG.md → PHASE1-WEEK3-013 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with the next Week 3 task (check BACKLOG.md — Week 3's
   draft list currently ends at PHASE1-WEEK3-013; confirm with the user whether Week 3
   is considered closed or has more tasks before inventing a new one)

## BLOCKERS
None yet identified — the tooltip-vs-popover and copy-scope questions above need
confirmation with the user before coding, same pattern as recent tasks.

## NOTES FOR NEXT TASK

**Training Config Builder (PHASE1-WEEK3-012) is done.** `app/(dashboard)/config/`
(`page.tsx` hosting `ConfigBuilder`, `[jobId]/page.tsx` as a read-only detail view) and
`components/training/*` (`MethodologyCard`, `ParameterField`, `JobStatusBadge`,
`TrainingControls`, `ConfigBuilder`) exist and work end-to-end against the real
backend, including two newly added backend routes: `GET /models/catalog` and
`GET /models/catalog/{model_id:path}`.

**Any future route taking a model-catalog-style ID as a path param needs the
`:path` converter** (`{model_id:path}`, not `{model_id}`) — real model IDs contain a
`/` (e.g. `meta-llama/Meta-Llama-3-8B`), which a plain path param cannot match. See
MEMORY.md ARCHITECTURE DECISIONS.

**`.github/workflows/ci.yml`'s `backend-test` job never runs `scripts/seed_data.py`** —
any test touching `model_catalog`/`gpu_pricing` rows must insert and clean up its own
rows directly via `psycopg2` (see `tests/test_model_catalog_routes.py`'s
`seeded_models` fixture), the same way dataset/job tests mock MinIO instead of hitting
it for real. Don't assume seeded reference data exists in CI or a fresh dev DB.

**This codebase's shadcn/ui setup uses base-ui's `render` prop, not the conventional
shadcn `asChild` prop**, and base-ui's `Select` is controlled via `value`/`onValueChange`
(confirmed again this session wiring `ConfigBuilder.tsx`'s base-model/dataset pickers via
RHF `Controller`) — `components/ui/tooltip.tsx` likely follows the same `render`-prop
convention as `dialog.tsx`/`select.tsx`; check its actual props before assuming
Radix-style `asChild` semantics.

**No browser-automation tool is available in this environment** (confirmed again
PHASE1-WEEK3-012). Established fallback: `npm run lint`/`npm run build` for
compile-time correctness, `curl` against a locally running backend for live API
contracts, and server-rendered HTML fetches to confirm pages mount without crashing.
State explicitly which parts are verified vs. traced-by-code-reading when a feature's
critical path is click/hover-only interactive.

**Gotcha, repeated across many sessions:** the PostToolUse hook
(`.claude/hooks/lint.py`) resolves paths relative to the Bash tool's current
working directory — a bare `cd apps/frontend && cmd` (no subshell parens) leaks the
cwd forward and breaks the hook on the next Edit/Write. Always wrap `cd`-then-run in
`(cd dir && cmd)`, or `cd` straight back to repo root immediately after a bare `cd`.

**Gotcha, environment-specific:** Docker containers (`fts_postgres`, `fts_redis`,
`fts_minio`, etc.) are NOT running by default between sessions — check `docker ps -a`
before assuming they're up, bring up only what's needed, and stop them again at the
end of the session. When running the backend locally outside Docker, override
`DATABASE_URL`/`DATABASE_URL_SYNC` → `localhost:5433`; `REDIS_URL` →
`redis://:fts_redis_dev_2024@localhost:6380/0`; MinIO needs `MINIO_HOST=localhost` +
`MINIO_PORT=9000` specifically (not `MINIO_ENDPOINT`). Also check `netstat -ano` for
stale processes already holding ports 3000/8000 before assuming a fresh
`npm run dev`/`uv run uvicorn` actually took effect.

**Gotcha, backend-specific:** the PostToolUse lint/format hook auto-fixes "unused"
imports between separate `Edit` calls on backend Python files — always add an import
and its first usage in the same `Edit`/`Write` call.

**LANDMINE, still unresolved (not relevant unless a future task touches
`training_engine/datasets/loader.py`):** `training_engine/datasets/` collides by name
with the pip-installed `datasets==2.19.0` (HuggingFace) library. Resolve before any
future `loader.py` work.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK3-012)
Completed 2026-06-20. User confirmed three scope questions before coding: add the
missing `GET /models/catalog` route now (rather than stub a free-text picker), wire
`POST /jobs` for real (not a pure skeleton), and build a broader parameter panel with
extra common ML params beyond the backend's minimal enforced set. Built the backend
model catalog route pair (including the `:path` converter fix for slash-containing
model IDs) plus 5 new tests that seed/clean up their own `model_catalog` rows since CI
never runs `seed_data.py`. Built the full frontend Config Builder: `MethodologyCard`,
`ParameterField`, `JobStatusBadge`, `TrainingControls`, and a `ConfigBuilder` form (RHF
+ Zod, methodology grid, base-model/dataset `Select`s, common + broader numeric fields
with pre-filled defaults, conditionally-rendered method-specific sections whose
required-ness mirrors the backend's `job_service.py` exactly) wired to a new
`hooks/useJobs.ts`/`hooks/useModelCatalog.ts`, plus `/config` and `/config/[jobId]`
pages. Verified: backend full suite 89/89 passing; frontend lint/build clean; live
end-to-end against a locally running backend with real seeded catalog data — confirmed
catalog list, catalog get with a real slash-containing model ID, and job creation all
work with the exact payload shape the form produces. Cleaned up the verification user
and restored all Docker containers/dev processes to their pre-session state. Pushed
`feat/PHASE1-WEEK3-012-config-builder`; PR not opened (manual creation per established
workflow).
