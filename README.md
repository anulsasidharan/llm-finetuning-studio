# LLM Fine-Tuning Studio

[![CI](https://github.com/anulsasidharan/llm-finetuning-studio/actions/workflows/ci.yml/badge.svg)](https://github.com/anulsasidharan/llm-finetuning-studio/actions)
[![License](https://img.shields.io/badge/license-TBD-lightgrey)](#license)
[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/node-20%2B-brightgreen)](https://nodejs.org/)

LLM Fine-Tuning Studio is an end-to-end web platform for LLM fine-tuning — taking a user from zero knowledge of fine-tuning all the way through to a deployed, production-ready model. It covers dataset preparation, methodology selection, training configuration, multi-cloud GPU orchestration, live training monitoring, evaluation, and deployment, all from a single UI.

<!-- screenshot -->

## Features

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

## Tech Stack

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

## Architecture

<!-- architecture diagram -->

## Quickstart

### Prerequisites

- Docker 24+
- Docker Compose 2.24+
- Node.js 20+
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (Python package manager)

### 1. Clone

```bash
git clone https://github.com/anulsasidharan/llm-finetuning-studio.git
cd llm-finetuning-studio
```

### 2. Configure

```bash
cp .env.example .env
# edit .env and fill in required values
```

### 3. Run

```bash
make setup   # installs deps, runs migrations, seeds data, installs git hooks
make dev     # starts the full stack via Docker Compose
```

Verify the backend is up:

```bash
curl http://localhost:8000/health
```

## Service URLs

| Service | URL | Container |
|---|---|---|
| Frontend | http://localhost:3000 | `fts_frontend` |
| Backend API | http://localhost:8000 | `fts_backend` |
| API Docs | http://localhost:8000/docs | `fts_backend` |
| PostgreSQL | localhost:5433 | `fts_postgres` |
| Redis | localhost:6380 | `fts_redis` |
| MinIO API | http://localhost:9000 | `fts_minio` |
| MinIO Console | http://localhost:9001 | `fts_minio` |
| Flower (Celery monitor) | http://localhost:5555 | `fts_flower` |

## Fine-Tuning Methods

| Method | Trainer Class | VRAM Usage | Min Samples | Key Differentiator |
|---|---|---|---|---|
| SFT | `trl.SFTTrainer` | Full model | 1,000 | Simplest; updates all weights |
| LoRA | `peft.LoraConfig` | ~40% of full | 500 | Low-rank adapters; frozen base |
| QLoRA | LoRA + `BitsAndBytesConfig` | ~15% of full | 500 | 4-bit NF4 base; most practical |
| DPO | `trl.DPOTrainer` | 2× LoRA | 1,000 pairs | Alignment without reward model |
| ORPO | `trl.ORPOTrainer` | ~LoRA | 1,000 pairs | Single-pass SFT + alignment |
| RLHF | `trl.PPOTrainer` | 4× base | 10,000 pairs | Gold standard alignment; complex |

## Project Structure

```
llm-finetuning-studio/
├── apps/
│   ├── frontend/          # Next.js 14 app
│   └── backend/           # FastAPI app
├── training_engine/       # ML package — GPU compute process
├── infra/                 # Docker, Terraform, K8s
├── docker-compose.yml
├── docker-compose.gpu.yml
├── Makefile
└── CLAUDE.md
```

## Development Commands

| Command | Description |
|---|---|
| `make setup` | First-time project setup (deps, migrations, seed, hooks) |
| `make dev` | Start all services (Docker) |
| `make dev-gpu` | Start all services with GPU support |
| `make stop` | Stop all services |
| `make build` | Rebuild all Docker images |
| `make migrate` | Run DB migrations |
| `make migration MSG="..."` | Create a new migration |
| `make seed` | Seed initial data |
| `make test` | Run all tests (frontend, backend, training engine) |
| `make lint` | Lint all code (report only) |
| `make format` | Format all code |
| `make check` | Lint + typecheck everything (mirrors CI) |
| `make fix` | Auto-fix all lint + format issues |
| `make logs` | Tail container logs |
| `make ps` | Show container status |
| `make clean` | Remove all containers + volumes |

Run `make help` for the full list at any time.

## Contributing

- Branch from `develop`, never from `main`.
- Name feature branches `feat/TASK-ID-description` (e.g. `feat/PHASE1-WEEK2-001-core-config`).
- Open all pull requests against `develop` using `.github/PULL_REQUEST_TEMPLATE.md`.
- `develop` merges to `main` only at the end of each phase milestone.
- Run `make check` before pushing — it mirrors what CI runs.

## License

Copyright © 2026 Anu Sasidharan / OrionVexa. All rights reserved. License terms to be determined.
