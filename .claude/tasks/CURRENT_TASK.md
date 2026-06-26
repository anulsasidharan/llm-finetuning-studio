# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE4-006
## TASK NAME: Production Docker Compose — docker-compose.prod.yml
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 4, Week 13
## BRANCH: feat/PHASE4-006-prod-docker-compose

## NEXT TASK
PHASE4-007 (GitHub Actions CI/CD pipeline).

## SUMMARY (this session, 2026-06-26)
Built a complete production Docker Compose stack and supporting files.

**Files created:**
- `docker-compose.prod.yml` — production compose; `production` build targets, no source
  volume mounts, no host port bindings for postgres/redis/minio, nginx on 80/443,
  `restart: always`, JSON logging with rotation, memory limits via `deploy.resources`,
  GPU training engine behind `--profile gpu`.
- `infra/docker/nginx/nginx.prod.conf` — nginx reverse proxy: `/api/` + `/health` +
  `/docs` → backend:8000; `/ws/` → backend:8000 with WebSocket upgrade; `/_next/static/`
  with 1-year immutable cache; everything else → frontend:3000. HTTPS server block
  commented out with cert mount instructions.
- `infra/docker/nginx/certs/.gitkeep` — placeholder dir for TLS certs with instructions.
- `apps/backend/start.prod.sh` — waits for DB, runs `alembic upgrade head`, starts
  uvicorn with 4 workers + `--proxy-headers`.
- `.env.prod.example` — production env template with all CHANGE_ME markers; storage
  Option A (MinIO) and Option B (AWS S3) both documented.

**Files modified:**
- `.gitignore` — added `.env.prod` so the real secrets file is never committed.
- `Makefile` — added `COMPOSE_PROD` variable and 8 prod targets: `prod-build`, `prod`,
  `prod-gpu`, `prod-stop`, `prod-migrate`, `prod-logs`, `prod-ps`, `prod-clean`.
  Each target guards against missing `.env.prod` where applicable.

**Validation:**
- `docker compose -f docker-compose.prod.yml config` exits 0 (only obsolete `version`
  warning, which was then removed from the file).

## GOTCHAS LOGGED
- `NEXT_PUBLIC_*` vars are baked into the Next.js bundle at build time — run
  `make prod-build` after updating the domain in `.env.prod`, not just `make prod`.
- GPU training engine is behind `profiles: [gpu]`; use `make prod-gpu` or
  `docker compose -f docker-compose.prod.yml --profile gpu up -d` to activate it.
- nginx `client_max_body_size 512m` matches `MAX_UPLOAD_SIZE_MB=500` in the env.
- `deploy.resources.limits` requires Docker Compose plugin v2+ (not Docker Compose v1 / standalone).
- `.env.prod` is gitignored; `.env.prod.example` is committed as the template.
