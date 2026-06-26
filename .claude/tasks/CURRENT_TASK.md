# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE4-002
## TASK NAME: Frontend: Learning Center — conceptual explainers
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 4, Week 13
## BRANCH: feat/PHASE4-002-learning-center

## NEXT TASK
PHASE4-003 (Email notifications — job complete/failed).

## SUMMARY (this session, 2026-06-26)
Built the Learning Center at `/learning` — permanent browsable reference for fine-tuning
concepts, complementary to the one-time Onboarding wizard.

**Frontend files created:**
- `apps/frontend/lib/learning-center-data.ts` — single content source: 17 topics across 4
  categories (Foundations, Datasets, Methodologies, Key concepts). Methodology articles are
  generated from shared `METHODOLOGY_INFO` plus local `METHODOLOGY_EXPLAINERS` enrichment
  (analogy, when-to-use bullets, watch-out callout) — no duplicate methods table.
- `apps/frontend/app/(dashboard)/learning/page.tsx` — server wrapper with `<Suspense>` for
  `useSearchParams` (Next.js 16 static prerender rule).
- `apps/frontend/app/(dashboard)/learning/LearningCenterView.tsx` — `"use client"` UI: left
  category/topic nav, right article panel with sections (heading/body/bullets/tip|info|warning
  callouts), methodology color badges, and "Try it in the studio" deep-links. Active topic via
  `?topic=<id>` (`router.replace` on nav click; defaults to `what-is-fine-tuning`).

**Frontend file modified:**
- `apps/frontend/components/layout/Sidebar.tsx` — added
  `{ label: "Learning Center", href: "/learning", icon: BookOpen }` after Onboarding.

**Topic inventory (17):**
- Foundations: what-is-fine-tuning, ft-vs-prompt-vs-rag, training-pipeline
- Datasets: dataset-formats, dataset-quality, preference-pairs
- Methodologies: sft, lora, qlora, dpo, orpo, rlhf (from `METHODOLOGY_INFO`)
- Concepts: lora-mechanics, vram-budgeting, loss-and-overfitting, alignment-overview

**Verification:**
- `npm run build` — passes (TypeScript clean, `/learning` prerenders as static `○`)
- No browser-automation tool available — topic nav switching not click-tested; SSR/build
  verification only (same standing limitation as prior frontend tasks)

## GOTCHAS LOGGED
- Learning Center topic ids for methodologies match `Methodology` literals (`sft`, `qlora`,
  etc.) — deep links like `/learning?topic=qlora` align with `/config?methodology=qlora`.
- `METHODOLOGY_EXPLAINERS` in `learning-center-data.ts` is display-only enrichment layered on
  `METHODOLOGY_INFO` — same pattern as onboarding's local title/color/VRAM maps; do not add a
  third parallel methods table elsewhere.
- Onboarding (`/onboarding`) remains the guided first-run walkthrough; Learning Center
  (`/learning`) is the always-available reference — intentionally separate routes.
