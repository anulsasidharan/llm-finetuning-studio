# ARCHITECTURE.md — System Design Reference
# Quick reference for how all parts of the system connect.

## REQUEST FLOW — Frontend to Database

Browser → Next.js (3000) → axios api client → FastAPI (8000) → Service → SQLAlchemy → PostgreSQL (5433)

## REQUEST FLOW — File Upload

Browser → Next.js → FastAPI /datasets/upload → core/storage.py → MinIO (9000)
                                              ↓
                                       datasets table (metadata only)

## TRAINING JOB FLOW

1. User submits config → POST /api/v1/jobs → job_service.create() → DB: status=queued
2. job_service triggers → Celery task (run_training_job) → Redis queue: training
3. Celery worker picks up task → dispatches to training_engine
4. training_engine trainer runs → MetricsCallback fires every N steps
5. MetricsCallback → Redis pub/sub channel: training_metrics:{job_id}
6. WebSocket hub (training_hub.py) → subscribed to Redis channel
7. WebSocket hub → pushes to browser via /ws/training/{job_id}
8. Frontend useTrainingWebSocket hook → receives metrics → updates Recharts

## COST ESTIMATION FLOW

User selects model + methodology + GPU + dataset size
→ POST /api/v1/gpu/estimate
→ cost_service.estimate(params)
→ reads GPU pricing from Redis cache (key: gpu:pricing, TTL: 1hr)
→ if cache miss: fetch from vendor APIs → store in Redis
→ returns EstimateResponse {hours, compute_cost, storage_cost, total}

## EXPORT FLOW (LoRA model)

POST /api/v1/registry/{id}/export-gguf
→ Celery task (export_tasks.export_gguf)
→ training_engine/export/merge_lora.py → merges adapter into base model
→ training_engine/export/export_gguf.py → calls llama.cpp convert binary
→ uploads .gguf to MinIO fts-exports bucket
→ updates model_registry.gguf_path

## AUTH FLOW

POST /auth/login → auth_service.authenticate() → bcrypt verify password
→ python-jose create JWT (access + refresh tokens)
→ client stores in httpOnly cookie (not localStorage)
→ all subsequent requests: Authorization: Bearer {token}
→ get_current_user dependency → decodes JWT → returns User ORM object

## CELERY QUEUES

Queue: training    → run_training_job tasks (long-running, GPU)
Queue: export      → export_gguf, push_hf tasks (medium, I/O heavy)
Queue: default     → short tasks (notifications, cache refresh)

## REDIS DATABASE ALLOCATION

DB 0: REDIS_URL              → general cache
DB 1: CELERY_BROKER_URL      → Celery task broker
DB 2: CELERY_RESULT_BACKEND  → Celery results
DB 3: TRAINING_PUBSUB_DB     → training metrics pub/sub channels

## MINIO BUCKET ALLOCATION

fts-datasets     → uploaded training datasets (JSONL, CSV, Parquet)
fts-models       → merged/final fine-tuned model weights
fts-checkpoints  → intermediate training checkpoints (auto-cleanup after 7 days)
fts-exports      → exported files (GGUF, quantized models)

## ENVIRONMENT — Inside Docker vs Outside

| Resource | Inside Docker | Outside Docker (host machine) |
|----------|--------------|-------------------------------|
| Postgres | postgres:5432 | localhost:5433 |
| Redis | redis:6379 | localhost:6380 |
| MinIO | minio:9000 | localhost:9000 |
| Backend | backend:8000 | localhost:8000 |
| Frontend | frontend:3000 | localhost:3000 |

Use the Docker internal hostnames in .env (containers talk to each other).
Use localhost:PORT when accessing from your host terminal or browser.

## TRAINING CONFIG STRUCTURE (JSONB in DB)

{
  "methodology": "qlora",
  "model": { "model_id": "...", "trust_remote_code": false },
  "dataset": { "format": "alpaca", "max_seq_length": 2048 },
  "quantization": { "load_in_4bit": true, "bnb_4bit_quant_type": "nf4" },
  "lora": { "r": 16, "lora_alpha": 32, "lora_dropout": 0.05, "target_modules": [...] },
  "training": { "num_train_epochs": 3, "learning_rate": 0.0002, ... },
  "artifacts": { "checkpoint_bucket": "fts-checkpoints", "push_to_hub_on_complete": false }
}
