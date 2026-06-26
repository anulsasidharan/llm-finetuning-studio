# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE4-007
## TASK NAME: GitHub Actions CI/CD pipeline
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 4, Week 13
## BRANCH: feat/PHASE4-007-cicd-pipeline
## PR: https://github.com/anulsasidharan/llm-finetuning-studio/pull/64

## NEXT TASK
PHASE4-008 (OrionVexa YouTube demo walkthrough video) — final task, no code required.

## SUMMARY (this session, 2026-06-26)
Built a complete GitHub Actions CI/CD pipeline with four workflow/config files.

**Files created/updated:**
- `.github/workflows/ci.yml` — updated with `uv` caching (`astral-sh/setup-uv@v4`
  `enable-cache: true`), new `frontend-build` job (`npm run build` after lint),
  `docker-build` jobs now use `docker/build-push-action@v5` with GHA layer cache.
- `.github/workflows/cd.yml` — new; triggers on push to `main`; builds backend and
  frontend production Docker images and pushes to
  `ghcr.io/<owner>/llm-finetuning-studio-{backend,frontend}` using
  `docker/build-push-action` + `docker/metadata-action` for SHA + `latest` tags;
  deploy job gated on `DEPLOY_ENABLED` repo variable + `production` environment.
- `.github/workflows/security.yml` — new; Trivy scans backend image, frontend image,
  and repo filesystem for CRITICAL/HIGH CVEs; SARIF uploaded to GitHub Security tab;
  runs on push to `main`/`develop` + weekly Monday 07:00 UTC cron.
- `.github/dependabot.yml` — new; weekly auto-updates for GitHub Actions, npm
  (Radix UI + TanStack grouped), backend pip, training-engine pip.

## GOTCHAS LOGGED
- CD `deploy` job requires `DEPLOY_ENABLED=true` repo variable + secrets
  `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_PATH` to activate.
- Frontend NEXT_PUBLIC_* vars for CD build come from repo variables
  (`vars.NEXT_PUBLIC_API_URL`, `vars.NEXT_PUBLIC_WS_URL`) — set in GitHub
  Settings → Variables → Actions before running CD on a real domain.
- Training engine is intentionally excluded from CD: GPU image (nvidia/cuda base)
  is ~8 GB and should be built on a GPU-equipped server, not GHA runners.
- `setup-uv@v4` (not v3 from old ci.yml) is needed for `enable-cache` to work.
- Trivy `exit-code: "0"` means scan failures are reported but don't fail the job;
  change to `"1"` to enforce hard gate on new CVEs.
