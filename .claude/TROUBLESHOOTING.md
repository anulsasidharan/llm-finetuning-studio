# TROUBLESHOOTING.md — Common Issues and Fixes

## DOCKER ISSUES

### Container fails to start
docker compose logs {service_name}
docker compose down -v && docker compose up -d    # Nuclear reset

### Port already in use
# This app uses offset ports: 5433 (postgres), 6380 (redis) to avoid conflicts.
# If still conflicting: lsof -i :5433 and kill the process, or change host port in docker-compose.yml.

### MinIO buckets not created
docker compose restart minio_init
# minio_init is a one-shot container — re-run it manually:
docker compose run --rm minio_init

### Database connection refused
# From host (terminal): use localhost:5433
# From inside Docker: use postgres:5432
# Check DATABASE_URL in .env uses the right host for context.

## BACKEND ISSUES

### Alembic migration fails — "table already exists"
alembic stamp head     # Mark current state without running migrations
alembic upgrade head   # Re-run

### Import errors in FastAPI startup
# Always use absolute imports from app root:
from models.user import User          ✅
from ..models.user import User        ❌

### Celery tasks not being picked up
docker compose logs celery_worker
# Check CELERY_BROKER_URL in .env matches redis container
# Verify task is registered: celery -A core.celery_app inspect registered

### JWT token expired errors in development
# ACCESS_TOKEN_EXPIRE_MINUTES=1440 (24 hours) — should be fine in dev
# If still expiring: check system clock sync in Docker

## FRONTEND ISSUES

### WebSocket not connecting
# Check NEXT_PUBLIC_WS_URL=ws://localhost:8000 in .env
# Verify backend is running: curl http://localhost:8000/health
# Check browser DevTools → Network → WS tab

### TanStack Query data stale
qc.invalidateQueries({ queryKey: ["your-key"] })    # Force refetch

### shadcn component not found
npx shadcn-ui@latest add {component-name}

### Type errors on API response
# Always match response types in types/index.ts to backend Pydantic schemas.
# Run: cd apps/frontend && npx tsc --noEmit to check type errors.

## TRAINING ENGINE ISSUES

### bitsandbytes error on Mac
# bitsandbytes requires Linux + NVIDIA GPU for QLoRA.
# On Mac: use CPU-mode SFT or LoRA only, skip load_in_4bit=True.
# Use docker-compose.gpu.yml only on Linux machines with NVIDIA GPU.

### HuggingFace gated model access denied
# Set HF_TOKEN in .env — must be a token from an account that accepted model terms.
# Accept terms at: https://huggingface.co/{model_id}

### CUDA out of memory
# Reduce per_device_train_batch_size to 1
# Enable gradient_checkpointing: true
# Reduce max_seq_length
# Use QLoRA instead of LoRA or full SFT

### Training metrics not appearing in dashboard
# Check Redis pub/sub: docker exec -it fts_redis redis-cli -a $REDIS_PASSWORD
# SUBSCRIBE training_metrics:{job_id}
# If no messages: check MetricsCallback is registered in trainer.callback list

## ENVIRONMENT ISSUES

### .env not loading
# Ensure .env is at repo root (next to docker-compose.yml)
# docker compose automatically loads .env from the same directory as the compose file
# For local dev outside Docker: python-dotenv loads from cwd

### Secret key errors
# Generate a proper key: openssl rand -hex 32
# Minimum 32 characters required for JWT signing

After every fix — update this file with what you tried and what worked.
Add a timestamp and brief description.
