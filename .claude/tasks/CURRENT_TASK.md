# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE1-WEEK1-001
## TASK NAME: Project Infrastructure Setup
## STATUS: IN PROGRESS
## ASSIGNED PHASE: Phase 1, Week 1

## OBJECTIVE
Set up the complete project skeleton — all directories, Docker containers, environment
configuration, and verify that all services start healthy before any feature code is written.

## ACCEPTANCE CRITERIA
- [ ] docker compose up starts cleanly with all 8 services healthy
- [ ] curl http://localhost:8000/health returns {"status":"healthy","database":"connected","redis":"connected","storage":"connected"}
- [ ] http://localhost:3000 loads the Next.js app without errors
- [ ] http://localhost:9001 opens MinIO console and the 4 buckets exist
- [ ] http://localhost:5555 opens Flower with 0 tasks
- [ ] alembic upgrade head runs with no errors
- [ ] scripts/seed_data.py runs and populates model catalog

## STEPS TO COMPLETE

### Step 1 — Directory scaffold
Run the mkdir commands from CLAUDE.md Section 8, Step 1.
Verify with: find . -type d | head -60

### Step 2 — Write docker-compose.yml
Copy exactly from CLAUDE.md Section 5. Do not modify ports or network names.

### Step 3 — Write docker-compose.gpu.yml
Copy exactly from CLAUDE.md Section 5.

### Step 4 — Write all Dockerfiles
- apps/backend/Dockerfile (3 stages: base, development, production)
- apps/frontend/Dockerfile (3 stages: base, development, builder, production)
- training_engine/Dockerfile (2 stages: development, gpu)
Copy exactly from CLAUDE.md Section 6.

### Step 5 — Write .env.example
Copy exactly from CLAUDE.md Section 4. Remove all real values — keep only keys and placeholder strings.

### Step 6 — Bootstrap frontend
Run commands from CLAUDE.md Section 8, Step 2.

### Step 7 — Bootstrap backend
Run commands from CLAUDE.md Section 8, Step 3.

### Step 8 — Bootstrap training engine
Run commands from CLAUDE.md Section 8, Step 4.

### Step 9 — Configure .env
cp .env.example .env
Generate SECRET_KEY: openssl rand -hex 32
Set POSTGRES_PASSWORD and REDIS_PASSWORD to strong values.

### Step 10 — Start and verify
Run commands from CLAUDE.md Section 8, Steps 5 and 6.
Check all acceptance criteria above.

## FILES TO CREATE IN THIS TASK
docker-compose.yml
docker-compose.gpu.yml
apps/backend/Dockerfile
apps/frontend/Dockerfile
training_engine/Dockerfile
.env.example
.gitignore
Makefile
(frontend bootstrap via npx create-next-app)
(backend bootstrap via uv + pip install)

## BLOCKERS
None

## NOTES FOR NEXT TASK
After this task: move to PHASE1-WEEK2-001 (Backend Core — config, database, auth, storage).
Update MEMORY.md session log before closing.
