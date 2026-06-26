# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE4-001
## TASK NAME: Frontend: Onboarding Wizard — beginner/advanced routing
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 4, Week 13
## BRANCH: feat/PHASE4-001-onboarding-wizard

## NEXT TASK
PHASE4-002 (Frontend: Learning Center — conceptual explainers).

## SUMMARY (this session, 2026-06-26)
Built the full Onboarding Wizard at `/onboarding` — first task of Phase 4.

**Frontend file created:**
- `apps/frontend/app/(dashboard)/onboarding/page.tsx` — multi-step client-side wizard with
  experience-level fork:
  - **Beginner path** (6 steps): experience → what-is-fine-tuning → methods reference →
    resources checklist → studio module tour → done (routes to `/datasets`)
  - **Advanced path** (4 steps): experience → methods reference → studio tour → done
    (routes to `/methodology`)
  - Method cards sourced from shared `lib/methodology-data.ts` `METHODOLOGY_INFO` (not a
    duplicate local table) with local display-only maps for full titles, VRAM labels, and
    per-methodology card colors
  - Studio tour lists 7 core pipeline modules (Datasets → Deploy) with click-through navigation
  - Progress bar, Back/Next/Finish nav, QLoRA beginner recommendation callout, advanced-path
    shortcut button to Methodology Selector

**Also fixed (unrelated regression on branch):**
- Reverted erroneous `asChild` additions on `deploy/page.tsx` `DialogTrigger` components —
  this codebase uses base-ui (`render` prop), not Radix `asChild`; the bad edit broke
  `npm run build` with a TypeScript error

**Verification:**
- `npm run build` — passes (TypeScript clean, `/onboarding` prerenders as static `○`)
- Sidebar already had `{ label: "Onboarding", href: "/onboarding", icon: Rocket }` from
  PHASE1-WEEK3-006 — no sidebar change needed
- Dashboard quick-start card at `/dashboard` already links to `/onboarding`
- No browser-automation tool available — wizard step transitions not click-tested; SSR/build
  verification only (same standing limitation as prior frontend tasks)

## GOTCHAS LOGGED
- Onboarding wizard state is purely in-component (`useState`) — no localStorage persistence of
  completion level or step index. Revisiting `/onboarding` always restarts at the experience
  picker. If a future task needs "skip onboarding" behavior, add explicit persistence then.
- Do not add `asChild` to `DialogTrigger`/`PopoverTrigger` in this codebase — use base-ui's
  `render={<Button ... />}` pattern (see MEMORY.md ARCHITECTURE DECISIONS).
