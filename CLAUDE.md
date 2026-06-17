# CLAUDE.md — LLM Fine-Tuning Studio

> **Project:** LLM Fine-Tuning Studio
> **Owner:** Anu Sasidharan · OrionVexa (orionvexa.ca)
> **GitHub:** https://github.com/anulsasidharan/llm-finetuning-studio
> **Version:** 1.0.0
> **Status:** In Development — Week 2 (Backend Core)

---

## ⚠️ CRITICAL ARCHITECTURE DECISION

This application is **100% standalone and independent**. It shares **nothing** with Unified RAG Studio:

- No shared database, auth service, containers, storage, Docker networks, env vars, or model registry
- No code imports from RAG Studio

Unified RAG Studio is used **only as a reference** for UI/UX patterns. Everything is rebuilt from scratch in this repo.

---

## 1. PROJECT OVERVIEW

LLM Fine-Tuning Studio is an end-to-end web platform for LLM fine-tuning — from zero knowledge to a deployed, production-ready fine-tuned model.

### Core Capabilities

- **Onboarding** — guided wizard with visual explainers for LoRA, QLoRA, SFT, DPO, ORPO, RLHF
- **Dataset Studio** — upload, format (Alpaca / ShareGPT / ChatML), quality-check, version datasets
- **Methodology Selector** — compare SFT, LoRA, QLoRA, DPO, ORPO, RLHF with auto-recommendation
- **Training Config Builder** — full parameter panel with inline contextual education
- **Multi-cloud GPU Selector** — compare and launch across AWS, GCP, Azure, RunPod, Lambda Labs
- **Cost Forecaster** — pre-flight cost estimation before any training job
- **Live Training Dashboard** — real-time loss curves, GPU utilization, ETA via WebSocket
- **Evaluation Playground** — side-by-side base vs fine-tuned model comparison with benchmarks
- **Experiment Tracker** — native versioning of runs, configs, metrics, and artifacts
- **Deploy & Export Manager** — GGUF, HuggingFace Hub push, vLLM deployment, REST endpoint generation

### Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS, shadcn/ui |
| Backend API | FastAPI, Python 3.11, Pydantic v2 |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 15 (dedicated instance) |
| Cache / Pub-Sub | Redis 7 (dedicated instance) |
| Storage | MinIO (local dev) → S3 (production) |
| ML Engine | HuggingFace Transformers, PEFT, TRL, BitsAndBytes, Accelerate |
| Containers | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## 2. DIRECTORY STRUCTURE

```
llm-finetuning-studio/
├── apps/
│   ├── frontend/                          # Next.js 14
│   │   ├── app/
│   │   │   ├── (auth)/login/page.tsx
│   │   │   ├── (auth)/register/page.tsx
│   │   │   ├── (auth)/layout.tsx
│   │   │   └── (dashboard)/
│   │   │       ├── layout.tsx             # Sidebar + Header wrapper
│   │   │       ├── page.tsx               # Dashboard home
│   │   │       ├── onboarding/page.tsx
│   │   │       ├── datasets/page.tsx
│   │   │       ├── datasets/upload/page.tsx
│   │   │       ├── datasets/[datasetId]/page.tsx
│   │   │       ├── methodology/page.tsx
│   │   │       ├── config/page.tsx
│   │   │       ├── config/[jobId]/page.tsx
│   │   │       ├── gpu-selector/page.tsx
│   │   │       ├── cost-estimator/page.tsx
│   │   │       ├── training/page.tsx
│   │   │       ├── training/[jobId]/page.tsx
│   │   │       ├── evaluation/page.tsx
│   │   │       ├── evaluation/[evalId]/page.tsx
│   │   │       ├── experiments/page.tsx
│   │   │       ├── experiments/[experimentId]/page.tsx
│   │   │       ├── models/page.tsx
│   │   │       ├── models/[modelId]/page.tsx
│   │   │       └── deploy/page.tsx
│   │   ├── components/
│   │   │   ├── ui/                        # shadcn/ui base components
│   │   │   ├── layout/                    # Sidebar, Header, Breadcrumb, PageContainer
│   │   │   ├── charts/                    # LossChart, LRScheduleChart, GPUUtilChart, VRAMChart, ThroughputChart
│   │   │   ├── training/                  # ConfigBuilder, ParameterField, ParameterTooltip, MethodologyCard, JobStatusBadge, TrainingControls
│   │   │   ├── dataset/                   # DatasetUploader, FormatSelector, QualityReport, DatasetPreview
│   │   │   ├── gpu/                       # GPUCard, VendorFilter, CostCard
│   │   │   └── shared/                    # EmptyState, LoadingSpinner, ErrorBoundary, ConfirmDialog, CopyButton
│   │   ├── hooks/                         # useTrainingJob, useCostEstimate, useGPUPricing, useDataset, useAuth
│   │   ├── lib/                           # api.ts, websocket.ts, store.ts, cost-estimator.ts, utils.ts
│   │   └── types/index.ts
│   │
│   └── backend/                           # FastAPI
│       ├── api/v1/routes/                 # auth, jobs, datasets, models, gpu, cost, experiments, registry, evaluation, deploy
│       ├── websocket/                     # training_hub.py, connection_manager.py
│       ├── core/                          # config, database, auth, security, storage, celery_app, exceptions
│       ├── models/                        # user, fine_tune_job, dataset, experiment, model_registry
│       ├── schemas/                       # auth, job, dataset, gpu, cost, experiment, registry
│       ├── services/                      # auth, job, dataset, cost, gpu, experiment, registry
│       ├── tasks/                         # training_tasks, export_tasks
│       ├── migrations/
│       ├── scripts/seed_data.py
│       ├── tests/
│       └── main.py
│
├── training_engine/                       # ML package — GPU compute process
│   ├── trainers/                          # base, sft, lora, qlora, dpo, orpo
│   ├── datasets/                          # loader, formatter, quality_check
│   ├── evaluation/                        # benchmark, compare
│   ├── export/                            # merge_lora, push_hf, export_gguf, quantize
│   ├── utils/                             # callbacks, gpu_monitor, cost_tracker
│   └── config/model_catalog.py
│
├── infra/
│   ├── docker/nginx/
│   ├── terraform/aws|gcp|azure/
│   └── k8s/
│
├── docker-compose.yml
├── docker-compose.gpu.yml
├── .env.example
├── Makefile
└── CLAUDE.md
```

---

## 3. SERVICES & PORTS

| Service | Container | Host Port | Purpose |
|---|---|---|---|
| PostgreSQL | fts_postgres | **5433** | App database |
| Redis | fts_redis | **6380** | Cache, Celery broker, pub/sub |
| MinIO | fts_minio | **9000** | Object storage |
| MinIO Console | fts_minio | **9001** | MinIO web UI |
| FastAPI Backend | fts_backend | **8000** | REST API + WebSocket |
| Next.js Frontend | fts_frontend | **3000** | Web UI |
| Flower | fts_flower | **5555** | Celery monitor |

All containers communicate over `fts_network`. Host port offsets (5433, 6380) avoid conflicts with other local services.

**Quick access:**
```
Frontend:      http://localhost:3000
Backend API:   http://localhost:8000
API Docs:      http://localhost:8000/docs
MinIO Console: http://localhost:9001
Flower:        http://localhost:5555
```

---

## 4. DATABASE SCHEMA

Tables: `users`, `datasets`, `fine_tune_jobs`, `experiments`, `experiment_runs`, `model_registry`

Key relationships:
- All tables cascade-delete on `user_id` FK
- `fine_tune_jobs` → `datasets` (optional FK)
- `experiment_runs` → `experiments` + `fine_tune_jobs`
- `model_registry` → `fine_tune_jobs` (optional FK)

Key fields on `fine_tune_jobs`: `status`, `base_model_id`, `methodology`, `training_config` (JSONB), `gpu_type`, `cloud_vendor`, live metrics (`train_loss`, `eval_loss`, `gpu_utilization_pct`, `vram_used_gb`, `tokens_per_second`), `estimated_cost_usd`, `actual_cost_usd`.

Indexes: `idx_jobs_user_id`, `idx_jobs_status`, `idx_datasets_user`, `idx_registry_user`

---

## 5. API ROUTES

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

## 6. CODING CONVENTIONS

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
- `.env` is never committed
- Secrets never hardcoded
- All endpoints require JWT auth unless explicitly `@public`
- File uploads: validate MIME type and size before writing to storage
- Training configs must pass schema validation before being queued

---

## 7. FINE-TUNING METHODOLOGY REFERENCE

| Method | Trainer Class | VRAM Usage | Min Samples | Key Differentiator |
|---|---|---|---|---|
| SFT | `trl.SFTTrainer` | Full model | 1,000 | Simplest; updates all weights |
| LoRA | `peft.LoraConfig` | ~40% of full | 500 | Low-rank adapters; frozen base |
| QLoRA | LoRA + `BitsAndBytesConfig` | ~15% of full | 500 | 4-bit NF4 base; most practical |
| DPO | `trl.DPOTrainer` | 2× LoRA | 1,000 pairs | Alignment without reward model |
| ORPO | `trl.ORPOTrainer` | ~LoRA | 1,000 pairs | Single-pass SFT + alignment |
| RLHF | `trl.PPOTrainer` | 4× base | 10,000 pairs | Gold standard alignment; complex |

---

## 8. PHASE 1 BUILD CHECKLIST

### Week 1 — Infrastructure & Skeleton ✅
- [x] Create repo on GitHub as `anulsasidharan/llm-finetuning-studio`
- [x] Directory scaffold complete
- [x] `docker-compose.yml`, `docker-compose.gpu.yml`, all Dockerfiles written
- [x] `.env` configured from `.env.example`
- [x] Infrastructure running: postgres, redis, minio, minio_init
- [x] Next.js 14 bootstrapped with all dependencies
- [x] Backend dependencies installed via uv
- [x] Training engine dependencies installed via uv

### Week 2 — Backend Core
- [ ] `core/config.py` — pydantic-settings env var config
- [ ] `core/database.py` — async SQLAlchemy engine + session factory
- [ ] SQLAlchemy ORM models for all tables
- [ ] Alembic initial migration applied
- [ ] `core/auth.py` + `core/security.py` — JWT logic
- [ ] `core/storage.py` — MinIO client wrapper
- [ ] `core/celery_app.py` — Celery config
- [ ] Auth endpoints: register, login, me, logout, refresh
- [ ] `GET /health` endpoint returning database + redis + storage status
- [ ] `scripts/seed_data.py` written and run
- [ ] `curl http://localhost:8000/health` returns 200

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

## 9. RESOURCES & REFERENCES

| Resource | URL |
|---|---|
| UI/UX reference (patterns only) | https://github.com/anulsasidharan/Unified-RAG-Studio |
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
