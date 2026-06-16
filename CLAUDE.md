# CLAUDE.md — LLM Fine-Tuning Studio

> **Project:** LLM Fine-Tuning Studio  
> **Type:** Fully Independent Standalone Application  
> **Base Inspiration:** Unified RAG Studio (UI/UX patterns only — NO shared code, services, or infrastructure)  
> **Owner:** Anu Sasidharan · OrionVexa (orionvexa.ca)  
> **GitHub Handle:** anulsasidharan  
> **Target Repo:** https://github.com/anulsasidharan/llm-finetuning-studio  
> **Version:** 1.0.0  
> **Status:** Pre-development — scaffold phase

---

## ⚠️ CRITICAL ARCHITECTURE DECISION

This application is **100% standalone and independent**. It shares **nothing** with Unified RAG Studio:

- ❌ No shared database
- ❌ No shared auth service
- ❌ No shared containers
- ❌ No shared storage buckets
- ❌ No shared Docker networks
- ❌ No shared environment variables
- ❌ No shared model registry
- ❌ No code imports from RAG Studio

The Unified RAG Studio repository is used **only as a reference** for UI/UX patterns, component design, and code style. Everything is rebuilt from scratch in this repo.

---

## 1. PROJECT OVERVIEW

LLM Fine-Tuning Studio is a one-stop-shop web platform for end-to-end LLM fine-tuning. Users can go from zero knowledge of fine-tuning all the way through to a fully deployed, production-ready fine-tuned model — entirely within this platform.

### Core Capabilities

- **Beginner to expert onboarding** — guided learning path with visual explainers for LoRA, QLoRA, SFT, DPO, ORPO, RLHF
- **Dataset Studio** — upload, format (Alpaca / ShareGPT / ChatML), quality-check, and version training datasets
- **Methodology Selector** — choose and compare SFT, LoRA, QLoRA, DPO, ORPO, RLHF with auto-recommendation
- **Training Config Builder** — full parameter panel with inline contextual education on every setting
- **Multi-cloud GPU Selector** — compare and launch GPU instances across AWS, GCP, Azure, RunPod, Lambda Labs
- **Cost Forecaster** — pre-flight cost estimation before submitting any training job
- **Live Training Dashboard** — real-time loss curves, GPU utilization, ETA via WebSocket
- **Evaluation Playground** — side-by-side base vs fine-tuned model comparison with benchmarks
- **Experiment Tracker** — native versioning of runs, configs, metrics, and artifacts
- **Deploy & Export Manager** — GGUF, HuggingFace Hub push, vLLM deployment, REST endpoint generation

### Tech Stack at a Glance

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| Backend API | FastAPI, Python 3.11, Pydantic v2 |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 15 (own dedicated instance) |
| Cache / Pub-Sub | Redis 7 (own dedicated instance) |
| Storage | MinIO (local dev) → S3 (production) |
| ML Engine | HuggingFace Transformers, PEFT, TRL, BitsAndBytes, Accelerate |
| Containers | Docker + Docker Compose (all services self-contained) |
| CI/CD | GitHub Actions |

---

## 2. REPOSITORY SETUP — FRESH START

This is a **brand new repository**. Do NOT clone Unified RAG Studio. Create from scratch.

### 2.1 Create New Repository

```bash
# Create a fresh project directory
mkdir llm-finetuning-studio
cd llm-finetuning-studio

# Initialize git
git init
git branch -M main

# Connect to remote (create the repo on GitHub first)
git remote add origin https://github.com/anulsasidharan/llm-finetuning-studio.git

# Create initial scaffold files
touch README.md CLAUDE.md .gitignore .env.example Makefile docker-compose.yml

# First commit
git add .
git commit -m "chore: initial project scaffold"
git push -u origin main

# Create development branch
git checkout -b develop
```

### 2.2 .gitignore

```gitignore
# Environment
.env
.env.local
.env.*.local
*.env

# Python
__pycache__/
*.py[cod]
*.pyo
.venv/
venv/
env/
*.egg-info/
dist/
build/
.pytest_cache/
.ruff_cache/
*.pyc

# Node
node_modules/
.next/
out/
npm-debug.log*
yarn-error.log*

# ML artifacts (large files — use S3/MinIO instead)
*.bin
*.safetensors
*.gguf
*.pt
*.ckpt
checkpoints/
runs/
wandb/

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Docker
.docker/

# Logs
*.log
logs/

# Terraform
infra/terraform/.terraform/
infra/terraform/*.tfstate
infra/terraform/*.tfstate.backup
infra/terraform/*.tfvars
```

---

## 3. COMPLETE DIRECTORY STRUCTURE

```
llm-finetuning-studio/
│
├── apps/
│   │
│   ├── frontend/                          # Next.js 14 — Fine-Tuning Studio UI
│   │   ├── app/
│   │   │   ├── (auth)/
│   │   │   │   ├── login/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── register/
│   │   │   │   │   └── page.tsx
│   │   │   │   └── layout.tsx
│   │   │   ├── (dashboard)/
│   │   │   │   ├── layout.tsx             # Sidebar + Header wrapper
│   │   │   │   ├── page.tsx               # Dashboard home / overview
│   │   │   │   ├── onboarding/
│   │   │   │   │   └── page.tsx           # Guided wizard — beginner entry point
│   │   │   │   ├── datasets/
│   │   │   │   │   ├── page.tsx           # Dataset list
│   │   │   │   │   ├── upload/
│   │   │   │   │   │   └── page.tsx       # Upload + format + quality check
│   │   │   │   │   └── [datasetId]/
│   │   │   │   │       └── page.tsx       # Dataset detail + preview
│   │   │   │   ├── methodology/
│   │   │   │   │   └── page.tsx           # Methodology selector wizard
│   │   │   │   ├── config/
│   │   │   │   │   ├── page.tsx           # Training config builder
│   │   │   │   │   └── [jobId]/
│   │   │   │   │       └── page.tsx       # Edit / clone existing config
│   │   │   │   ├── gpu-selector/
│   │   │   │   │   └── page.tsx           # GPU + cloud vendor comparison
│   │   │   │   ├── cost-estimator/
│   │   │   │   │   └── page.tsx           # Pre-flight cost calculator
│   │   │   │   ├── training/
│   │   │   │   │   ├── page.tsx           # All training jobs list
│   │   │   │   │   └── [jobId]/
│   │   │   │   │       └── page.tsx       # Live training dashboard
│   │   │   │   ├── evaluation/
│   │   │   │   │   ├── page.tsx           # Evaluation runs list
│   │   │   │   │   └── [evalId]/
│   │   │   │   │       └── page.tsx       # Side-by-side eval playground
│   │   │   │   ├── experiments/
│   │   │   │   │   ├── page.tsx           # Experiment list
│   │   │   │   │   └── [experimentId]/
│   │   │   │   │       └── page.tsx       # Experiment detail + run compare
│   │   │   │   ├── models/
│   │   │   │   │   ├── page.tsx           # Fine-tuned model registry
│   │   │   │   │   └── [modelId]/
│   │   │   │   │       └── page.tsx       # Model detail + deploy options
│   │   │   │   └── deploy/
│   │   │   │       └── page.tsx           # Deploy & export manager
│   │   │   ├── api/                       # Next.js API routes (thin proxies to FastAPI)
│   │   │   │   └── [...path]/
│   │   │   │       └── route.ts
│   │   │   ├── globals.css
│   │   │   ├── layout.tsx                 # Root layout
│   │   │   └── page.tsx                   # Landing / redirect
│   │   ├── components/
│   │   │   ├── ui/                        # shadcn/ui base components
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   ├── Breadcrumb.tsx
│   │   │   │   └── PageContainer.tsx
│   │   │   ├── charts/
│   │   │   │   ├── LossChart.tsx          # Training + eval loss curves
│   │   │   │   ├── LRScheduleChart.tsx    # Learning rate over steps
│   │   │   │   ├── GPUUtilChart.tsx       # GPU utilization % over time
│   │   │   │   ├── VRAMChart.tsx          # VRAM usage over time
│   │   │   │   └── ThroughputChart.tsx    # Tokens/sec over time
│   │   │   ├── training/
│   │   │   │   ├── ConfigBuilder.tsx      # Multi-section training form
│   │   │   │   ├── ParameterField.tsx     # Input + tooltip wrapper
│   │   │   │   ├── ParameterTooltip.tsx   # Contextual help popover
│   │   │   │   ├── MethodologyCard.tsx    # SFT/LoRA/QLoRA/DPO card
│   │   │   │   ├── JobStatusBadge.tsx
│   │   │   │   └── TrainingControls.tsx   # Pause / Resume / Cancel
│   │   │   ├── dataset/
│   │   │   │   ├── DatasetUploader.tsx    # Drag-drop file upload
│   │   │   │   ├── FormatSelector.tsx     # Alpaca / ShareGPT / ChatML
│   │   │   │   ├── QualityReport.tsx      # Quality check results display
│   │   │   │   └── DatasetPreview.tsx     # Formatted sample rows
│   │   │   ├── gpu/
│   │   │   │   ├── GPUCard.tsx            # Single GPU instance card
│   │   │   │   ├── VendorFilter.tsx       # AWS/GCP/Azure/RunPod filter
│   │   │   │   └── CostCard.tsx           # Estimated cost breakdown card
│   │   │   └── shared/
│   │   │       ├── EmptyState.tsx
│   │   │       ├── LoadingSpinner.tsx
│   │   │       ├── ErrorBoundary.tsx
│   │   │       ├── ConfirmDialog.tsx
│   │   │       └── CopyButton.tsx
│   │   ├── hooks/
│   │   │   ├── useTrainingJob.ts          # WebSocket + job control
│   │   │   ├── useCostEstimate.ts         # Live cost calculation
│   │   │   ├── useGPUPricing.ts           # GPU pricing from backend
│   │   │   ├── useDataset.ts              # Dataset CRUD operations
│   │   │   └── useAuth.ts                 # Auth state + token refresh
│   │   ├── lib/
│   │   │   ├── api.ts                     # Typed axios client
│   │   │   ├── websocket.ts               # WebSocket client wrapper
│   │   │   ├── store.ts                   # Zustand global stores
│   │   │   ├── cost-estimator.ts          # Cost calculation logic
│   │   │   └── utils.ts                   # cn(), formatDuration(), etc.
│   │   ├── types/
│   │   │   └── index.ts                   # All shared TypeScript types
│   │   ├── public/
│   │   │   ├── favicon.ico
│   │   │   └── logo.svg
│   │   ├── next.config.ts
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   ├── .eslintrc.json
│   │   ├── .prettierrc
│   │   └── package.json
│   │
│   └── backend/                           # FastAPI — REST API + WebSocket hub
│       ├── api/
│       │   └── v1/
│       │       ├── routes/
│       │       │   ├── __init__.py
│       │       │   ├── auth.py
│       │       │   ├── jobs.py
│       │       │   ├── datasets.py
│       │       │   ├── models.py
│       │       │   ├── gpu.py
│       │       │   ├── cost.py
│       │       │   ├── experiments.py
│       │       │   ├── registry.py
│       │       │   ├── evaluation.py
│       │       │   └── deploy.py
│       │       └── __init__.py
│       ├── websocket/
│       │   ├── __init__.py
│       │   ├── training_hub.py
│       │   └── connection_manager.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── database.py
│       │   ├── auth.py
│       │   ├── security.py
│       │   ├── storage.py
│       │   ├── celery_app.py
│       │   └── exceptions.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py
│       │   ├── fine_tune_job.py
│       │   ├── dataset.py
│       │   ├── experiment.py
│       │   └── model_registry.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── auth.py
│       │   ├── job.py
│       │   ├── dataset.py
│       │   ├── gpu.py
│       │   ├── cost.py
│       │   ├── experiment.py
│       │   └── registry.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── auth_service.py
│       │   ├── job_service.py
│       │   ├── dataset_service.py
│       │   ├── cost_service.py
│       │   ├── gpu_service.py
│       │   ├── experiment_service.py
│       │   └── registry_service.py
│       ├── tasks/
│       │   ├── __init__.py
│       │   ├── training_tasks.py
│       │   └── export_tasks.py
│       ├── migrations/
│       │   ├── versions/
│       │   ├── env.py
│       │   └── script.py.mako
│       ├── scripts/
│       │   └── seed_data.py
│       ├── tests/
│       │   ├── conftest.py
│       │   ├── test_auth.py
│       │   ├── test_jobs.py
│       │   └── test_datasets.py
│       ├── main.py
│       ├── requirements.txt
│       ├── requirements-dev.txt
│       ├── alembic.ini
│       ├── Dockerfile
│       └── .python-version
│
├── training_engine/                       # Python ML package — GPU compute process
│   ├── trainers/
│   │   ├── __init__.py
│   │   ├── base_trainer.py
│   │   ├── sft_trainer.py
│   │   ├── lora_trainer.py
│   │   ├── qlora_trainer.py
│   │   ├── dpo_trainer.py
│   │   └── orpo_trainer.py
│   ├── datasets/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── formatter.py
│   │   └── quality_check.py
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── benchmark.py
│   │   └── compare.py
│   ├── export/
│   │   ├── __init__.py
│   │   ├── merge_lora.py
│   │   ├── push_hf.py
│   │   ├── export_gguf.py
│   │   └── quantize.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── callbacks.py
│   │   ├── gpu_monitor.py
│   │   └── cost_tracker.py
│   ├── config/
│   │   ├── __init__.py
│   │   └── model_catalog.py
│   ├── tests/
│   │   ├── conftest.py
│   │   └── test_formatters.py
│   ├── __init__.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .python-version
│
├── infra/
│   ├── docker/
│   │   └── nginx/
│   │       └── nginx.conf
│   ├── terraform/
│   │   ├── aws/main.tf
│   │   ├── gcp/main.tf
│   │   └── azure/main.tf
│   └── k8s/
│       ├── vllm-deployment.yaml
│       ├── vllm-service.yaml
│       └── hpa.yaml
│
├── docker-compose.yml                     # Full local dev stack
├── docker-compose.gpu.yml                 # GPU training add-on
├── docker-compose.prod.yml                # Production (no hot-reload)
├── .env.example
├── Makefile
├── README.md
└── CLAUDE.md                              # This file
```

---

## 4. ENVIRONMENT VARIABLES

Create `.env` at repo root by copying `.env.example`. This file is **never committed to git**.

```env
# ═══════════════════════════════════════════════════════════════
# LLM FINE-TUNING STUDIO — Environment Configuration
# Copy this file to .env and fill in all values
# NEVER commit .env to git
# ═══════════════════════════════════════════════════════════════

# ─── App ────────────────────────────────────────────────────────
APP_NAME="LLM Fine-Tuning Studio"
ENVIRONMENT=development
LOG_LEVEL=DEBUG
SECRET_KEY=change-this-to-a-random-64-character-string-use-openssl-rand-hex-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
REFRESH_TOKEN_EXPIRE_DAYS=30

# ─── PostgreSQL (standalone — dedicated to this app only) ────────
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=fts_user
POSTGRES_PASSWORD=fts_password_change_in_production
POSTGRES_DB=fts_db
DATABASE_URL=postgresql+asyncpg://fts_user:fts_password_change_in_production@postgres:5432/fts_db
DATABASE_URL_SYNC=postgresql://fts_user:fts_password_change_in_production@postgres:5432/fts_db

# ─── Redis (standalone — dedicated to this app only) ─────────────
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis_password_change_in_production
REDIS_URL=redis://:redis_password_change_in_production@redis:6379/0
CELERY_BROKER_URL=redis://:redis_password_change_in_production@redis:6379/1
CELERY_RESULT_BACKEND=redis://:redis_password_change_in_production@redis:6379/2
TRAINING_PUBSUB_DB=redis://:redis_password_change_in_production@redis:6379/3

# ─── MinIO (local S3-compatible storage — dev only) ──────────────
MINIO_HOST=minio
MINIO_PORT=9000
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin_change_in_production
MINIO_ENDPOINT=http://minio:9000
MINIO_USE_SSL=false

# Storage bucket names (auto-created on startup)
BUCKET_DATASETS=fts-datasets
BUCKET_MODELS=fts-models
BUCKET_CHECKPOINTS=fts-checkpoints
BUCKET_EXPORTS=fts-exports

# ─── AWS S3 (production — replaces MinIO) ───────────────────────
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_DATASETS=fts-datasets-prod
S3_BUCKET_MODELS=fts-models-prod
S3_BUCKET_CHECKPOINTS=fts-checkpoints-prod
S3_BUCKET_EXPORTS=fts-exports-prod

# ─── HuggingFace ────────────────────────────────────────────────
HF_TOKEN=hf_xxxx
HF_WRITE_TOKEN=hf_xxxx
HF_CACHE_DIR=/app/.cache/huggingface

# ─── Cloud GPU Vendors ──────────────────────────────────────────
RUNPOD_API_KEY=
LAMBDA_LABS_API_KEY=
CLOUD_AWS_ACCESS_KEY_ID=
CLOUD_AWS_SECRET_ACCESS_KEY=
CLOUD_GCP_SERVICE_ACCOUNT_JSON=
CLOUD_AZURE_SUBSCRIPTION_ID=
CLOUD_AZURE_CLIENT_ID=
CLOUD_AZURE_CLIENT_SECRET=
CLOUD_AZURE_TENANT_ID=

# ─── GPU Pricing ────────────────────────────────────────────────
GPU_PRICING_CACHE_TTL_SECONDS=3600

# ─── Notifications (optional) ───────────────────────────────────
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
NOTIFICATION_FROM_EMAIL=noreply@orionvexa.ca
SLACK_WEBHOOK_URL=

# ─── Training Engine ────────────────────────────────────────────
MAX_UPLOAD_SIZE_MB=500
TRAINING_CHECKPOINT_INTERVAL_STEPS=200
TRAINING_METRICS_PUSH_INTERVAL_SECONDS=5
TRAINING_ENGINE_REDIS_URL=redis://:redis_password_change_in_production@redis:6379/3

# ─── Frontend (Next.js public vars — safe for browser) ──────────
NEXT_PUBLIC_APP_NAME="LLM Fine-Tuning Studio"
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

---

## 5. DOCKER COMPOSE — COMPLETE STANDALONE STACK

Every service runs in its own container on a private Docker network named `fts_network`. Nothing is shared with or reachable from any other application on the host.

```yaml
version: "3.9"

name: llm-finetuning-studio

networks:
  fts_network:
    driver: bridge
    name: fts_network

volumes:
  fts_postgres_data:
    name: fts_postgres_data
  fts_redis_data:
    name: fts_redis_data
  fts_minio_data:
    name: fts_minio_data
  fts_hf_cache:
    name: fts_hf_cache

services:

  # ─── PostgreSQL ───────────────────────────────────────────────
  postgres:
    image: postgres:15-alpine
    container_name: fts_postgres
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      PGDATA: /var/lib/postgresql/data/pgdata
    ports:
      - "5433:5432"             # Host 5433 — avoids conflict with any other Postgres
    volumes:
      - fts_postgres_data:/var/lib/postgresql/data
    networks:
      - fts_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s

  # ─── Redis ────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    container_name: fts_redis
    restart: unless-stopped
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --appendonly yes
      --appendfsync everysec
    ports:
      - "6380:6379"             # Host 6380 — avoids conflict with any other Redis
    volumes:
      - fts_redis_data:/data
    networks:
      - fts_network
    healthcheck:
      test: ["CMD", "redis-cli", "-a", "${REDIS_PASSWORD}", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── MinIO (S3-compatible object storage — dev) ───────────────
  minio:
    image: minio/minio:latest
    container_name: fts_minio
    restart: unless-stopped
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    ports:
      - "9000:9000"             # S3 API
      - "9001:9001"             # MinIO web console
    volumes:
      - fts_minio_data:/data
    networks:
      - fts_network
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─── MinIO bucket initializer (one-shot) ──────────────────────
  minio_init:
    image: minio/mc:latest
    container_name: fts_minio_init
    depends_on:
      minio:
        condition: service_healthy
    networks:
      - fts_network
    env_file: .env
    entrypoint: >
      /bin/sh -c "
      mc alias set fts http://minio:9000 ${MINIO_ROOT_USER} ${MINIO_ROOT_PASSWORD};
      mc mb --ignore-existing fts/${BUCKET_DATASETS};
      mc mb --ignore-existing fts/${BUCKET_MODELS};
      mc mb --ignore-existing fts/${BUCKET_CHECKPOINTS};
      mc mb --ignore-existing fts/${BUCKET_EXPORTS};
      echo 'MinIO buckets initialized.';
      exit 0;
      "

  # ─── Backend API (FastAPI) ────────────────────────────────────
  backend:
    build:
      context: ./apps/backend
      dockerfile: Dockerfile
      target: development
    container_name: fts_backend
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    volumes:
      - ./apps/backend:/app
      - fts_hf_cache:/app/.cache/huggingface
    networks:
      - fts_network
    command: >
      sh -c "alembic upgrade head &&
             uvicorn main:app --reload --host 0.0.0.0 --port 8000"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s

  # ─── Celery Worker ────────────────────────────────────────────
  celery_worker:
    build:
      context: ./apps/backend
      dockerfile: Dockerfile
      target: development
    container_name: fts_celery_worker
    restart: unless-stopped
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - ./apps/backend:/app
      - ./training_engine:/training_engine
      - fts_hf_cache:/app/.cache/huggingface
    networks:
      - fts_network
    command: >
      celery -A core.celery_app worker
      --loglevel=info
      --queues=training,export,default
      --concurrency=2

  # ─── Celery Beat (scheduled tasks — GPU pricing refresh) ──────
  celery_beat:
    build:
      context: ./apps/backend
      dockerfile: Dockerfile
      target: development
    container_name: fts_celery_beat
    restart: unless-stopped
    env_file: .env
    depends_on:
      - redis
    volumes:
      - ./apps/backend:/app
    networks:
      - fts_network
    command: celery -A core.celery_app beat --loglevel=info

  # ─── Flower (Celery monitor — dev only) ───────────────────────
  flower:
    image: mher/flower:2.0
    container_name: fts_flower
    restart: unless-stopped
    ports:
      - "5555:5555"
    environment:
      CELERY_BROKER_URL: ${CELERY_BROKER_URL}
      FLOWER_BASIC_AUTH: admin:admin
    depends_on:
      - redis
    networks:
      - fts_network

  # ─── Frontend (Next.js) ───────────────────────────────────────
  frontend:
    build:
      context: ./apps/frontend
      dockerfile: Dockerfile
      target: development
    container_name: fts_frontend
    restart: unless-stopped
    ports:
      - "3000:3000"
    env_file: .env
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_WS_URL: ws://localhost:8000
    depends_on:
      backend:
        condition: service_healthy
    volumes:
      - ./apps/frontend:/app
      - /app/node_modules
      - /app/.next
    networks:
      - fts_network
    command: npm run dev
```

### `docker-compose.gpu.yml` (local GPU training add-on)

```yaml
# Usage: docker compose -f docker-compose.yml -f docker-compose.gpu.yml up

version: "3.9"

services:
  training_engine:
    build:
      context: ./training_engine
      dockerfile: Dockerfile
      target: gpu
    container_name: fts_training_engine
    restart: unless-stopped
    env_file: .env
    environment:
      CUDA_VISIBLE_DEVICES: "0"
    depends_on:
      - redis
      - minio
    volumes:
      - ./training_engine:/training_engine
      - fts_hf_cache:/training_engine/.cache/huggingface
    networks:
      - fts_network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    command: >
      celery -A worker.celery_app worker
      --loglevel=info
      --queues=gpu_training
      --concurrency=1
```

---

## 6. DOCKERFILES

### `apps/backend/Dockerfile`

```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
RUN apt-get update && apt-get install -y curl gcc libpq-dev && rm -rf /var/lib/apt/lists/*
RUN pip install uv

FROM base AS development
COPY requirements.txt requirements-dev.txt ./
RUN uv pip install --system -r requirements.txt -r requirements-dev.txt
EXPOSE 8000

FROM base AS production
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### `apps/frontend/Dockerfile`

```dockerfile
FROM node:20-alpine AS base
WORKDIR /app

FROM base AS development
COPY package.json package-lock.json* ./
RUN npm ci
EXPOSE 3000
CMD ["npm", "run", "dev"]

FROM base AS builder
COPY package.json package-lock.json* ./
RUN npm ci
COPY . .
RUN npm run build

FROM base AS production
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

### `training_engine/Dockerfile`

```dockerfile
FROM python:3.11-slim AS development
WORKDIR /training_engine
RUN apt-get update && apt-get install -y curl gcc git && rm -rf /var/lib/apt/lists/*
RUN pip install uv
COPY requirements.txt ./
RUN uv pip install --system -r requirements.txt
COPY . .

FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu22.04 AS gpu
WORKDIR /training_engine
RUN apt-get update && apt-get install -y python3.11 python3-pip git curl && rm -rf /var/lib/apt/lists/*
RUN pip install uv
COPY requirements.txt ./
RUN uv pip install --system torch==2.3.0 torchvision torchaudio \
    --index-url https://download.pytorch.org/whl/cu121
RUN uv pip install --system -r requirements.txt
COPY . .
```

---

## 7. SERVICES & PORTS REFERENCE

| Service | Container Name | Internal Port | Host Port | Purpose |
|---|---|---|---|---|
| PostgreSQL | fts_postgres | 5432 | **5433** | App database (offset to avoid host conflicts) |
| Redis | fts_redis | 6379 | **6380** | Cache, Celery broker, pub/sub (offset to avoid conflicts) |
| MinIO | fts_minio | 9000 | **9000** | Object storage — datasets, models, checkpoints |
| MinIO Console | fts_minio | 9001 | **9001** | MinIO web UI |
| FastAPI Backend | fts_backend | 8000 | **8000** | REST API + WebSocket hub |
| Next.js Frontend | fts_frontend | 3000 | **3000** | Web UI |
| Celery Worker | fts_celery_worker | — | — | Async training + export job processor |
| Celery Beat | fts_celery_beat | — | — | Scheduled tasks (pricing refresh) |
| Flower | fts_flower | 5555 | **5555** | Celery task monitor dashboard |

All containers communicate exclusively over `fts_network`. No service is reachable from outside except through the explicit host port bindings above.

---

## 8. INITIAL SETUP COMMANDS

Execute in order. Claude Code must follow this sequence exactly on first setup.

### Step 1 — Create fresh repo and scaffold directories

```bash
mkdir llm-finetuning-studio && cd llm-finetuning-studio
git init && git branch -M main
git remote add origin https://github.com/anulsasidharan/llm-finetuning-studio.git

mkdir -p \
  apps/frontend/app/\(auth\)/login \
  apps/frontend/app/\(auth\)/register \
  apps/frontend/app/\(dashboard\)/onboarding \
  apps/frontend/app/\(dashboard\)/datasets/upload \
  apps/frontend/app/\(dashboard\)/methodology \
  apps/frontend/app/\(dashboard\)/config \
  apps/frontend/app/\(dashboard\)/gpu-selector \
  apps/frontend/app/\(dashboard\)/cost-estimator \
  apps/frontend/app/\(dashboard\)/training \
  apps/frontend/app/\(dashboard\)/evaluation \
  apps/frontend/app/\(dashboard\)/experiments \
  apps/frontend/app/\(dashboard\)/models \
  apps/frontend/app/\(dashboard\)/deploy \
  apps/frontend/components/ui \
  apps/frontend/components/layout \
  apps/frontend/components/charts \
  apps/frontend/components/training \
  apps/frontend/components/dataset \
  apps/frontend/components/gpu \
  apps/frontend/components/shared \
  apps/frontend/hooks \
  apps/frontend/lib \
  apps/frontend/types \
  apps/frontend/public \
  apps/backend/api/v1/routes \
  apps/backend/websocket \
  apps/backend/core \
  apps/backend/models \
  apps/backend/schemas \
  apps/backend/services \
  apps/backend/tasks \
  apps/backend/migrations/versions \
  apps/backend/scripts \
  apps/backend/tests \
  training_engine/trainers \
  training_engine/datasets \
  training_engine/evaluation \
  training_engine/export \
  training_engine/utils \
  training_engine/config \
  training_engine/tests \
  infra/docker/nginx \
  infra/terraform/aws \
  infra/terraform/gcp \
  infra/terraform/azure \
  infra/k8s
```

### Step 2 — Frontend setup

```bash
cd apps/frontend

npx create-next-app@latest . \
  --typescript --tailwind --eslint --app \
  --src-dir=false --import-alias="@/*" --no-git

npm install \
  @tanstack/react-query@^5 @tanstack/react-query-devtools@^5 \
  zustand@^4 socket.io-client@^4 recharts@^2 \
  axios@^1 react-hook-form@^7 @hookform/resolvers@^3 zod@^3 \
  lucide-react@^0.400 date-fns@^3 clsx tailwind-merge \
  class-variance-authority next-themes \
  @radix-ui/react-tooltip @radix-ui/react-tabs @radix-ui/react-dialog \
  @radix-ui/react-select @radix-ui/react-slider @radix-ui/react-switch \
  @radix-ui/react-progress @radix-ui/react-scroll-area \
  @radix-ui/react-separator @radix-ui/react-popover \
  @radix-ui/react-label @radix-ui/react-dropdown-menu @radix-ui/react-avatar

npm install -D prettier @tailwindcss/forms @tailwindcss/typography

npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input label select slider switch tabs \
  dialog tooltip badge progress table form textarea separator skeleton \
  alert scroll-area command popover dropdown-menu avatar sheet

cd ../..
```

### Step 3 — Backend setup

```bash
cd apps/backend

uv venv .venv --python 3.11
source .venv/bin/activate

uv pip install \
  fastapi==0.111.0 uvicorn[standard]==0.29.0 \
  pydantic==2.7.0 pydantic-settings==2.3.0 \
  sqlalchemy[asyncio]==2.0.30 asyncpg==0.29.0 alembic==1.13.1 \
  python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 \
  python-multipart==0.0.9 httpx==0.27.0 \
  celery[redis]==5.4.0 redis==5.0.4 \
  boto3==1.34.0 minio==7.2.7 \
  python-dotenv==1.0.1 structlog==24.2.0 \
  tenacity==8.3.0 aiofiles==23.2.1

uv pip install -D pytest==8.2.0 pytest-asyncio==0.23.7 \
  pytest-cov==5.0.0 faker==25.2.0 ruff==0.4.4

uv pip freeze > requirements.txt
echo "3.11" > .python-version
alembic init migrations

cd ../..
```

### Step 4 — Training engine setup

```bash
cd training_engine

uv venv .venv --python 3.11
source .venv/bin/activate

# CPU-only torch for development (use cu121 URL on GPU machines)
uv pip install torch==2.3.0 torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cpu

uv pip install \
  transformers==4.41.0 peft==0.11.0 trl==0.8.6 \
  datasets==2.19.0 evaluate==0.4.2 accelerate==0.30.0 \
  sentencepiece==0.2.0 huggingface_hub==0.23.0 \
  tokenizers==0.19.1 safetensors scipy scikit-learn einops \
  redis==5.0.4 celery[redis]==5.4.0 \
  boto3==1.34.0 minio==7.2.7 \
  pynvml==11.5.0 psutil==5.9.8 \
  structlog==24.2.0 python-dotenv==1.0.1 lm-eval==0.4.2

# GPU-only extras (install only on Linux with NVIDIA GPU):
# uv pip install bitsandbytes==0.43.1
# uv pip install unsloth

uv pip freeze > requirements.txt
echo "3.11" > .python-version

cd ..
```

### Step 5 — Configure environment and start

```bash
cp .env.example .env
# Open .env and set SECRET_KEY, POSTGRES_PASSWORD, REDIS_PASSWORD at minimum

docker compose up -d postgres redis minio minio_init
sleep 15
docker compose ps      # Verify all healthy

docker compose run --rm backend alembic upgrade head
docker compose run --rm backend python -m scripts.seed_data
```

### Step 6 — Verify and run

```bash
# Check health
curl http://localhost:8000/health
# Expected: {"status":"healthy","database":"connected","redis":"connected","storage":"connected"}

# Start full stack
docker compose up

# Access points:
# Frontend:      http://localhost:3000
# Backend API:   http://localhost:8000
# API Docs:      http://localhost:8000/docs
# MinIO Console: http://localhost:9001
# Flower:        http://localhost:5555
```

---

## 9. DATABASE SCHEMA

All tables belong exclusively to this application.

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255),
    is_active       BOOLEAN NOT NULL DEFAULT true,
    is_superuser    BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE datasets (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id           UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name              VARCHAR(255) NOT NULL,
    description       TEXT,
    format            VARCHAR(50),
    source            VARCHAR(50),
    hf_dataset_id     VARCHAR(255),
    storage_path      VARCHAR(500),
    file_size_bytes   BIGINT,
    num_samples       INTEGER,
    avg_input_tokens  FLOAT,
    avg_output_tokens FLOAT,
    language          VARCHAR(10) DEFAULT 'en',
    quality_score     FLOAT,
    quality_issues    JSONB,
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE fine_tune_jobs (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id               UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name                  VARCHAR(255) NOT NULL,
    description           TEXT,
    status                VARCHAR(50) NOT NULL DEFAULT 'draft',
    base_model_id         VARCHAR(255) NOT NULL,
    base_model_size_b     FLOAT NOT NULL,
    methodology           VARCHAR(50) NOT NULL,
    dataset_id            UUID REFERENCES datasets(id),
    dataset_split         JSONB DEFAULT '{"train":0.9,"val":0.05,"test":0.05}',
    training_config       JSONB NOT NULL DEFAULT '{}',
    gpu_type              VARCHAR(100),
    cloud_vendor          VARCHAR(50),
    cloud_instance_id     VARCHAR(255),
    cloud_job_id          VARCHAR(255),
    gpu_count             INTEGER DEFAULT 1,
    estimated_cost_usd    DECIMAL(10,4),
    actual_cost_usd       DECIMAL(10,4),
    cost_per_hour         DECIMAL(8,4),
    current_step          INTEGER DEFAULT 0,
    total_steps           INTEGER,
    current_epoch         FLOAT DEFAULT 0,
    total_epochs          INTEGER,
    train_loss            FLOAT,
    eval_loss             FLOAT,
    learning_rate         FLOAT,
    tokens_per_second     FLOAT,
    gpu_utilization_pct   FLOAT,
    vram_used_gb          FLOAT,
    vram_total_gb         FLOAT,
    checkpoint_path       VARCHAR(500),
    output_model_path     VARCHAR(500),
    hf_model_id           VARCHAR(255),
    started_at            TIMESTAMPTZ,
    completed_at          TIMESTAMPTZ,
    estimated_completion  TIMESTAMPTZ,
    error_message         TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE experiments (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name        VARCHAR(255) NOT NULL,
    description TEXT,
    tags        TEXT[],
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE experiment_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id   UUID NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    job_id          UUID NOT NULL REFERENCES fine_tune_jobs(id),
    run_number      INTEGER NOT NULL,
    notes           TEXT,
    metrics_summary JSONB,
    config_snapshot JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE model_registry (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    job_id          UUID REFERENCES fine_tune_jobs(id),
    name            VARCHAR(255) NOT NULL,
    description     TEXT,
    base_model_id   VARCHAR(255) NOT NULL,
    methodology     VARCHAR(50) NOT NULL,
    artifact_path   VARCHAR(500),
    gguf_path       VARCHAR(500),
    hf_model_id     VARCHAR(255),
    status          VARCHAR(50) DEFAULT 'available',
    deployment_url  VARCHAR(500),
    tags            TEXT[],
    eval_results    JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_user_id  ON fine_tune_jobs(user_id);
CREATE INDEX idx_jobs_status   ON fine_tune_jobs(status);
CREATE INDEX idx_datasets_user ON datasets(user_id);
CREATE INDEX idx_registry_user ON model_registry(user_id);
```

---

## 10. API ROUTES

```
GET    /health

POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
POST   /api/v1/auth/logout

GET    /api/v1/datasets
POST   /api/v1/datasets/upload
POST   /api/v1/datasets/{id}/format
POST   /api/v1/datasets/{id}/quality-check
GET    /api/v1/datasets/{id}/preview
DELETE /api/v1/datasets/{id}

GET    /api/v1/models/catalog
GET    /api/v1/models/catalog/{model_id}

GET    /api/v1/jobs
POST   /api/v1/jobs
GET    /api/v1/jobs/{job_id}
PATCH  /api/v1/jobs/{job_id}
DELETE /api/v1/jobs/{job_id}
GET    /api/v1/jobs/{job_id}/metrics
GET    /api/v1/jobs/{job_id}/config

GET    /api/v1/gpu/instances
GET    /api/v1/gpu/pricing
POST   /api/v1/gpu/estimate

GET    /api/v1/experiments
POST   /api/v1/experiments
GET    /api/v1/experiments/{id}
POST   /api/v1/experiments/{id}/runs
GET    /api/v1/experiments/{id}/compare

GET    /api/v1/registry
GET    /api/v1/registry/{id}
POST   /api/v1/registry/{id}/push-hf
POST   /api/v1/registry/{id}/export-gguf
POST   /api/v1/registry/{id}/deploy-vllm
DELETE /api/v1/registry/{id}

POST   /api/v1/eval/compare
POST   /api/v1/eval/benchmark

WS     /ws/training/{job_id}
```

---

## 11. MAKEFILE

```makefile
.PHONY: help dev stop build setup migrate migration seed test lint format clean logs ps

COMPOSE = docker compose
BACKEND = apps/backend
FRONTEND = apps/frontend
TRAINING = training_engine

help:
	@echo "make setup      First-time project setup"
	@echo "make dev        Start all services (Docker)"
	@echo "make stop       Stop all services"
	@echo "make build      Rebuild all Docker images"
	@echo "make migrate    Run DB migrations"
	@echo "make migration  Create migration (MSG=your message)"
	@echo "make seed       Seed initial data"
	@echo "make test       Run all tests"
	@echo "make lint       Lint all code"
	@echo "make format     Format all code"
	@echo "make logs       Tail container logs"
	@echo "make ps         Show container status"
	@echo "make clean      Remove all containers + volumes"

setup:
	cp -n .env.example .env || true
	cd $(FRONTEND) && npm install
	cd $(BACKEND) && uv venv .venv --python 3.11 && \
	  . .venv/bin/activate && uv pip install -r requirements.txt
	cd $(TRAINING) && uv venv .venv --python 3.11 && \
	  . .venv/bin/activate && uv pip install -r requirements.txt
	$(COMPOSE) up -d postgres redis minio minio_init
	sleep 15
	$(COMPOSE) run --rm backend alembic upgrade head
	$(COMPOSE) run --rm backend python -m scripts.seed_data
	@echo "✅ Setup complete. Run 'make dev' to start."

dev:
	$(COMPOSE) up

dev-gpu:
	$(COMPOSE) -f docker-compose.yml -f docker-compose.gpu.yml up

stop:
	$(COMPOSE) down

build:
	$(COMPOSE) build --no-cache

ps:
	$(COMPOSE) ps

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) run --rm backend alembic upgrade head

migration:
	$(COMPOSE) run --rm backend alembic revision --autogenerate -m "$(MSG)"

seed:
	$(COMPOSE) run --rm backend python -m scripts.seed_data

db-shell:
	docker exec -it fts_postgres psql -U fts_user -d fts_db

redis-cli:
	docker exec -it fts_redis redis-cli -a $$REDIS_PASSWORD

minio-ui:
	open http://localhost:9001 || xdg-open http://localhost:9001

test:
	cd $(FRONTEND) && npm run test
	cd $(BACKEND) && . .venv/bin/activate && pytest tests/ -v --cov=.
	cd $(TRAINING) && . .venv/bin/activate && pytest tests/ -v

lint:
	cd $(FRONTEND) && npm run lint
	cd $(BACKEND) && . .venv/bin/activate && ruff check .
	cd $(TRAINING) && . .venv/bin/activate && ruff check .

format:
	cd $(FRONTEND) && npx prettier --write .
	cd $(BACKEND) && . .venv/bin/activate && ruff format .
	cd $(TRAINING) && . .venv/bin/activate && ruff format .

clean:
	$(COMPOSE) down -v --remove-orphans
	rm -rf $(FRONTEND)/.next $(FRONTEND)/node_modules
	rm -rf $(BACKEND)/.venv $(TRAINING)/.venv
	@echo "✅ Clean complete."
```

---

## 12. CODING CONVENTIONS

### Python (backend + training engine)
- **Package manager:** `uv` — always `uv pip install`, never bare `pip`
- **Formatter / Linter:** `ruff format` and `ruff check`
- **Type hints:** Required on every function signature
- **Async:** All DB and I/O operations must be async
- **Config:** All env vars loaded via `pydantic-settings` Settings class only
- **Logging:** `structlog` with JSON output — never use `print()`
- **Exceptions:** Custom hierarchy in `core/exceptions.py`

### TypeScript / React (frontend)
- **Router:** Next.js App Router only — never Pages Router
- **Components:** Functional + hooks only
- **Server vs Client:** Default RSC; `"use client"` only for interactivity
- **State:** TanStack Query for server state; Zustand for global client state; RHF+Zod for forms
- **API calls:** Typed axios client in `lib/api.ts` only
- **Styling:** Tailwind utilities only — no inline styles

### General
- `.env` is never committed — `.gitignore` enforces this
- Secrets never hardcoded
- All endpoints require JWT auth unless explicitly decorated `@public`
- File uploads: validate MIME type and size before writing to storage
- Training configs must pass schema validation before being queued

---

## 13. FINE-TUNING METHODOLOGY QUICK REFERENCE

| Method | Trainer Class | VRAM Usage | Min Samples | Key Differentiator |
|---|---|---|---|---|
| SFT | `trl.SFTTrainer` | Full model | 1,000 | Simplest; updates all weights |
| LoRA | `peft.LoraConfig` | ~40% of full | 500 | Low-rank adapters; frozen base |
| QLoRA | LoRA + `BitsAndBytesConfig` | ~15% of full | 500 | 4-bit NF4 base; most practical |
| DPO | `trl.DPOTrainer` | 2× LoRA (reference model) | 1,000 pairs | Alignment without reward model |
| ORPO | `trl.ORPOTrainer` | ~LoRA | 1,000 pairs | Single-pass SFT + alignment |
| RLHF | `trl.PPOTrainer` | 4× base | 10,000 pairs | Gold standard alignment; complex |

---

## 14. PHASE 1 BUILD CHECKLIST

### Week 1 — Infrastructure & Skeleton
- [ ] Create repo on GitHub as `anulsasidharan/llm-finetuning-studio`
- [ ] Run directory scaffold (Section 8, Step 1)
- [ ] Write `docker-compose.yml`, `docker-compose.gpu.yml`, all Dockerfiles
- [ ] Copy and configure `.env` from `.env.example`
- [ ] Start infrastructure: `docker compose up -d postgres redis minio minio_init`
- [ ] Verify all containers healthy: `docker compose ps`
- [ ] Bootstrap Next.js 14 app (Section 8, Step 2)
- [ ] Install backend deps with uv (Section 8, Step 3)
- [ ] Install training engine deps (Section 8, Step 4)

### Week 2 — Backend Core
- [ ] Implement `core/config.py` with all env var settings
- [ ] Implement `core/database.py` async SQLAlchemy engine
- [ ] Write all SQLAlchemy ORM models
- [ ] Configure Alembic and run initial migration
- [ ] Implement `core/auth.py` + `core/security.py`
- [ ] Implement `core/storage.py` MinIO client
- [ ] Implement `core/celery_app.py`
- [ ] Implement auth endpoints (register, login, me)
- [ ] Implement `GET /health` endpoint
- [ ] Write and run `scripts/seed_data.py`
- [ ] Verify `curl http://localhost:8000/health` returns 200

### Week 3 — Dataset + Config + Frontend Shell
- [ ] Dataset upload endpoint with MinIO integration
- [ ] Dataset format + quality check services
- [ ] Fine-tune job creation with config validation
- [ ] Next.js sidebar layout with all module routes
- [ ] Login + register pages with Zod validation
- [ ] Dataset Studio page (upload, format, quality report)
- [ ] Training Config Builder skeleton
- [ ] `ParameterTooltip` component
- [ ] `useAuth` hook with token storage and refresh

---

## 15. RESOURCES & REFERENCES

| Resource | URL |
|---|---|
| UI/UX reference (patterns only — no code sharing) | https://github.com/anulsasidharan/Unified-RAG-Studio |
| HuggingFace PEFT | https://huggingface.co/docs/peft |
| TRL (SFT/DPO/ORPO/PPO) | https://huggingface.co/docs/trl |
| BitsAndBytes | https://huggingface.co/docs/bitsandbytes |
| Unsloth | https://github.com/unslothai/unsloth |
| RunPod API | https://docs.runpod.io/reference/api |
| Lambda Labs API | https://cloud.lambdalabs.com/api/v1/docs |
| lm-evaluation-harness | https://github.com/EleutherAI/lm-evaluation-harness |
| MinIO Python SDK | https://min.io/docs/minio/linux/developers/python/API.html |
| QLoRA paper | https://arxiv.org/abs/2305.14314 |
| LoRA paper | https://arxiv.org/abs/2106.09685 |
| DPO paper | https://arxiv.org/abs/2305.18290 |
| ORPO paper | https://arxiv.org/abs/2403.07691 |
| OrionVexa GitHub | https://github.com/anulsasidharan |
| OrionVexa YouTube | https://www.youtube.com/@OrionVexa |

---

*This CLAUDE.md is the single source of truth for all development on LLM Fine-Tuning Studio. Every Claude Code session must read this file first before taking any action.*
