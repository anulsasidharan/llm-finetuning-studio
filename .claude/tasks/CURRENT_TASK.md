# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK1-002
## TASK NAME: Makefile Verification + README.md
## STATUS: IN PROGRESS
## ASSIGNED PHASE: Phase 1, Week 1
## BRANCH: feat/PHASE1-WEEK1-002-makefile-readme

## OBJECTIVE
Verify the Makefile commands are correct and functional, then write the project README.md
with a complete quickstart guide so any developer can clone and run the full stack in minutes.

## ACCEPTANCE CRITERIA
- [ ] `make help` prints all available commands without error
- [ ] `make ps` shows all Docker container states
- [ ] `make logs` tails container logs correctly
- [ ] `make lint` runs ruff on backend + training_engine without crashing
- [ ] README.md exists at repo root with all sections below
- [ ] README.md quickstart section walks from `git clone` to running stack in < 15 steps
- [ ] README.md includes port reference table
- [ ] README.md includes tech stack table

## STEPS TO COMPLETE

### Step 1 — Cut feature branch
```
git checkout develop
git pull origin develop
git checkout -b feat/PHASE1-WEEK1-002-makefile-readme
```

### Step 2 — Verify Makefile targets
Run each command and confirm it works:
```
make help
make ps
```
Fix any broken Makefile targets. Note: `make dev`, `make build`, `make test` are NOT
run in this task (they require full Docker or test infrastructure).

### Step 3 — Smoke test lint targets
```
cd apps/backend && uv run ruff check . 2>&1 | head -20
cd training_engine && uv run ruff check . 2>&1 | head -20
```
Fix any obvious ruff errors in bootstrap files. Do not add config files beyond what exists.

### Step 4 — Write README.md
Create `README.md` at repo root with these sections:
1. Title + badges (build status, license, Python version, Node version)
2. One-paragraph description of the platform
3. Screenshot placeholder (<!-- screenshot -->)
4. Features list (10 bullet points from CLAUDE.md Section 1)
5. Tech Stack table (from CLAUDE.md Section 1)
6. Architecture diagram placeholder (<!-- architecture diagram -->)
7. Quickstart — Prerequisites (Docker 24+, Docker Compose 2.24+, Node 20+, Python 3.11+, uv)
8. Quickstart — 1-2-3 clone/configure/run steps
9. Service URLs table (all 7 ports from MEMORY.md PORT MAP)
10. Fine-Tuning Methods table (from CLAUDE.md Section 13)
11. Project Structure (condensed tree — top 3 levels only)
12. Development Commands (make help output summarized)
13. Contributing section (branch naming, PR to develop)
14. License section

### Step 5 — Stage, commit, push
```
git add README.md Makefile
git status  # verify only README.md and Makefile are staged
git commit -m "docs(readme): PHASE1-WEEK1-002 add README and verify Makefile"
git push origin feat/PHASE1-WEEK1-002-makefile-readme
```

### Step 6 — Update tracking files
1. CURRENT_TASK.md → mark STATUS: ✅ COMPLETE, all criteria [x]
2. DONE.md → add row for PHASE1-WEEK1-002
3. BACKLOG.md → PHASE1-WEEK1-002 ✅ DONE
4. MEMORY.md → update session log
5. CURRENT_TASK.md → replace with PHASE1-WEEK2-001 content (core/config.py full implementation)

## FILES TO CREATE IN THIS TASK
- README.md (repo root)

## FILES TO VERIFY/UPDATE IN THIS TASK
- Makefile (verify existing targets work; fix if needed)

## BLOCKERS
None

## NOTES FOR NEXT TASK
After this task: move to PHASE1-WEEK2-001 through PHASE1-WEEK2-013 (Backend Core).
Priority order: config → database → ORM models → alembic migration → security → auth →
storage → celery_app → exceptions → main.py full → health → auth routes → seed_data.
The celery_worker and celery_beat containers are restarting because core/celery_app.py
doesn't exist yet — PHASE1-WEEK2-008 creates it and fixes that restart loop.

## PREVIOUS TASK SUMMARY (PHASE1-WEEK1-001)
Completed 2026-06-15. All 8 Docker services healthy. 79 files committed.
Key decisions made during that task:
- backend start.sh created to fix DB DNS timing issue on container startup
- psycopg2-binary added to requirements.txt for alembic sync migrations
- alembic.ini uses postgres:5432 (Docker-internal) not localhost:5433
- shadcn init required npm_config_legacy_peer_deps=true due to Next.js 16 peer deps
