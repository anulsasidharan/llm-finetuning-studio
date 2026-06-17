# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK2-001
## TASK NAME: core/config.py — pydantic-settings, all env vars
## STATUS: ⬜ TODO
## ASSIGNED PHASE: Phase 1, Week 2
## BRANCH: feat/PHASE1-WEEK2-001-core-config

## OBJECTIVE
Extend `apps/backend/core/config.py` so the `Settings` class covers every variable in
`.env.example` (backend-relevant ones only — skip `NEXT_PUBLIC_*` frontend vars), add a
cached settings accessor, and confirm the app still boots with the expanded config.

## ACCEPTANCE CRITERIA
- [ ] Every backend-relevant var in `.env.example` has a typed field in `Settings`
      (REFRESH_TOKEN_EXPIRE_DAYS, AWS_*, S3_BUCKET_*, RUNPOD_API_KEY, LAMBDA_LABS_API_KEY,
      CLOUD_AWS_*, CLOUD_GCP_*, CLOUD_AZURE_*, GPU_PRICING_CACHE_TTL_SECONDS, SMTP_*,
      NOTIFICATION_FROM_EMAIL, SLACK_WEBHOOK_URL, TRAINING_CHECKPOINT_INTERVAL_STEPS,
      TRAINING_METRICS_PUSH_INTERVAL_SECONDS, TRAINING_ENGINE_REDIS_URL)
- [ ] `get_settings()` cached accessor added (`functools.lru_cache`) — `settings` module-level
      singleton kept for backward compatibility with existing imports
- [ ] All fields have correct types (str / int / bool) and sane defaults where the value is
      genuinely optional (API keys, SMTP creds); required secrets stay required (no default)
- [ ] `uv run python -c "from core.config import settings; print(settings.APP_NAME)"` runs
      without raising a validation error (using repo `.env`)
- [ ] `uv run ruff check .` and `uv run ruff format --check .` pass on `apps/backend`
- [ ] No `os.environ` direct access anywhere in `apps/backend` (grep to confirm)

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK2-001-core-config
```

### Step 2 — Read current state
Read `apps/backend/core/config.py` and `.env.example` side by side. List every var present
in `.env.example` that has no matching field in `Settings`.

### Step 3 — Extend Settings
Add the missing fields grouped with comments matching `.env.example` section headers
(App / Postgres / Redis / MinIO / AWS S3 / HuggingFace / Cloud GPU Vendors / GPU Pricing /
Notifications / Training Engine). Keep `case_sensitive=True` and `extra="ignore"`.

### Step 4 — Add cached accessor
```python
from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

### Step 5 — Verify
```
cd apps/backend
uv run python -c "from core.config import settings; print(settings.APP_NAME)"
uv run ruff check .
uv run ruff format --check .
```

### Step 6 — Stage, commit, push
```
git add apps/backend/core/config.py
git commit -m "feat(config): PHASE1-WEEK2-001 cover all env vars in Settings"
git push origin feat/PHASE1-WEEK2-001-core-config
```

### Step 7 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK2-001
3. BACKLOG.md → PHASE1-WEEK2-001 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-002 content (core/database.py)

## FILES TO UPDATE IN THIS TASK
- apps/backend/core/config.py

## BLOCKERS
None

## NOTES FOR NEXT TASK
After this task: PHASE1-WEEK2-002 (core/database.py — async SQLAlchemy engine + session
factory) depends directly on the finished Settings class for DATABASE_URL. Continue down
the Week 2 backlog in dependency order: config → database → ORM models → alembic migration
→ security → auth → storage → celery_app → exceptions → main.py → health → auth routes →
seed_data. The celery_worker and celery_beat containers are still restarting because
core/celery_app.py doesn't exist yet (PHASE1-WEEK2-008 fixes that).

## PREVIOUS TASK SUMMARY (PHASE1-WEEK1-003, gitignore audit)
Completed 2026-06-17. BACKLOG.md had already marked this DONE from the original template,
and a working .gitignore already existed from the WEEK1-001 scaffold — so this pass was an
audit, not a from-scratch write. Verified via `git status --ignored` and `git ls-files` that
no build artifacts were accidentally tracked and no new pattern collided with a tracked file.
Closed real gaps: test coverage artifacts (`.coverage`, `htmlcov/`, `coverage.xml` — backend
uses pytest-cov), Celery beat schedule files, Windows OS files (Thumbs.db, desktop.ini),
generic temp/backup files, private key/cert files (`*.pem`, `*.key`), an extra Terraform
artifact (`*.tfplan`), and Claude Code's `.claude/settings.local.json` local override.
Confirmed `apps/frontend/.gitignore` (from create-next-app) already covers Next.js-specific
patterns (`.pnp`, `.vercel`, `*.tsbuildinfo`, `next-env.d.ts`) — left as-is, no duplication
needed at root. Committed and pushed to feat/PHASE1-WEEK1-003-gitignore.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK1-002)
Completed 2026-06-17. Verified Makefile (`make` binary not installed in this Windows/Git
Bash environment — verified by running the underlying shell commands directly: `docker
compose ps`, `docker compose logs`, `ruff check` on backend + training_engine, all passed
cleanly; Makefile recipe indentation confirmed to use tabs, not spaces). No Makefile changes
were needed. Wrote full README.md at repo root (badges, features, tech stack, quickstart,
service URL table, fine-tuning methods table, project structure, dev commands, contributing,
license placeholder). Committed and pushed to feat/PHASE1-WEEK1-002-makefile-readme.
