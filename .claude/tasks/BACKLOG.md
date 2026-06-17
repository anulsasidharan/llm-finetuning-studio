# TASK BACKLOG — LLM Fine-Tuning Studio
# Move tasks to CURRENT_TASK.md when starting. Update status here when done.

## PHASE 1 — Foundation (Weeks 1–3)

### Week 1 — Infrastructure
| ID | Task | Status | Depends On | Branch Name |
|----|------|--------|------------|-------------|
| PHASE1-WEEK1-001 | Project scaffold + Docker stack + all services healthy | ✅ DONE | — | feat/PHASE1-WEEK1-001-project-scaffold |
| PHASE1-WEEK1-002 | Makefile verification + README.md quickstart | 🔄 IN PROGRESS | PHASE1-WEEK1-001 | feat/PHASE1-WEEK1-002-makefile-readme |
| PHASE1-WEEK1-003 | Write .gitignore | ✅ DONE | PHASE1-WEEK1-001 | feat/PHASE1-WEEK1-003-gitignore |
| PHASE1-WEEK1-004 | Write README.md with quickstart | ⬜ TODO | PHASE1-WEEK1-001 | feat/PHASE1-WEEK1-004-readme |

### Week 2 — Backend Core
| ID | Task | Status | Depends On |
|----|------|--------|------------|
| PHASE1-WEEK2-001 | core/config.py — pydantic-settings all env vars | ⬜ TODO | PHASE1-WEEK1-001 |
| PHASE1-WEEK2-002 | core/database.py — async SQLAlchemy engine + session | ⬜ TODO | PHASE1-WEEK2-001 |
| PHASE1-WEEK2-003 | All ORM models (user, fine_tune_job, dataset, experiment, model_registry) | ⬜ TODO | PHASE1-WEEK2-002 |
| PHASE1-WEEK2-004 | Alembic config + initial migration | ⬜ TODO | PHASE1-WEEK2-003 |
| PHASE1-WEEK2-005 | core/security.py — bcrypt password hashing | ⬜ TODO | PHASE1-WEEK2-001 |
| PHASE1-WEEK2-006 | core/auth.py — JWT create + verify + get_current_user dependency | ⬜ TODO | PHASE1-WEEK2-005 |
| PHASE1-WEEK2-007 | core/storage.py — MinIO client + upload/download/presigned URL | ⬜ TODO | PHASE1-WEEK2-001 |
| PHASE1-WEEK2-008 | core/celery_app.py — Celery app + queue routing | ⬜ TODO | PHASE1-WEEK2-001 |
| PHASE1-WEEK2-009 | core/exceptions.py — custom exception hierarchy | ⬜ TODO | PHASE1-WEEK2-001 |
| PHASE1-WEEK2-010 | main.py — FastAPI app factory + router registration + CORS | ⬜ TODO | PHASE1-WEEK2-006 |
| PHASE1-WEEK2-011 | GET /health endpoint | ⬜ TODO | PHASE1-WEEK2-010 |
| PHASE1-WEEK2-012 | Auth routes — POST /register, /login, /refresh, GET /me | ⬜ TODO | PHASE1-WEEK2-006 |
| PHASE1-WEEK2-013 | scripts/seed_data.py — model catalog + GPU pricing | ⬜ TODO | PHASE1-WEEK2-004 |

### Week 3 — Dataset + Config + Frontend Shell
| ID | Task | Status | Depends On |
|----|------|--------|------------|
| PHASE1-WEEK3-001 | Dataset ORM service + upload endpoint | ⬜ TODO | PHASE1-WEEK2-007 |
| PHASE1-WEEK3-002 | training_engine/datasets/formatter.py — Alpaca/ShareGPT/ChatML | ⬜ TODO | — |
| PHASE1-WEEK3-003 | training_engine/datasets/quality_check.py — dedup, stats, language | ⬜ TODO | — |
| PHASE1-WEEK3-004 | POST /datasets/{id}/format + /quality-check endpoints | ⬜ TODO | PHASE1-WEEK3-002 |
| PHASE1-WEEK3-005 | Fine-tune job creation endpoint + config validation | ⬜ TODO | PHASE1-WEEK2-010 |
| PHASE1-WEEK3-006 | Frontend: Next.js root layout + sidebar + header | ⬜ TODO | PHASE1-WEEK1-001 |
| PHASE1-WEEK3-007 | Frontend: lib/api.ts typed axios client | ⬜ TODO | PHASE1-WEEK3-006 |
| PHASE1-WEEK3-008 | Frontend: types/index.ts all shared types | ⬜ TODO | PHASE1-WEEK3-006 |
| PHASE1-WEEK3-009 | Frontend: hooks/useAuth.ts with token refresh | ⬜ TODO | PHASE1-WEEK3-007 |
| PHASE1-WEEK3-010 | Frontend: login + register pages with Zod validation | ⬜ TODO | PHASE1-WEEK3-009 |
| PHASE1-WEEK3-011 | Frontend: Dataset Studio page — upload + format + quality report | ⬜ TODO | PHASE1-WEEK3-007 |
| PHASE1-WEEK3-012 | Frontend: Config Builder skeleton — all sections rendered | ⬜ TODO | PHASE1-WEEK3-007 |
| PHASE1-WEEK3-013 | Frontend: ParameterTooltip component | ⬜ TODO | PHASE1-WEEK3-012 |

## PHASE 2 — Training Engine + Core Modules (Weeks 4–8)

| ID | Task | Status | Depends On |
|----|------|--------|------------|
| PHASE2-001 | training_engine/trainers/base_trainer.py | ⬜ TODO | PHASE1 complete |
| PHASE2-002 | training_engine/trainers/sft_trainer.py | ⬜ TODO | PHASE2-001 |
| PHASE2-003 | training_engine/trainers/lora_trainer.py | ⬜ TODO | PHASE2-001 |
| PHASE2-004 | training_engine/trainers/qlora_trainer.py | ⬜ TODO | PHASE2-003 |
| PHASE2-005 | training_engine/trainers/dpo_trainer.py | ⬜ TODO | PHASE2-001 |
| PHASE2-006 | training_engine/trainers/orpo_trainer.py | ⬜ TODO | PHASE2-001 |
| PHASE2-007 | training_engine/utils/callbacks.py — MetricsCallback → Redis pub/sub | ⬜ TODO | PHASE2-001 |
| PHASE2-008 | training_engine/utils/gpu_monitor.py — pynvml metrics | ⬜ TODO | PHASE2-001 |
| PHASE2-009 | Celery training task — dispatch to training engine | ⬜ TODO | PHASE2-007 |
| PHASE2-010 | WebSocket hub — subscribe Redis channel, push to browser | ⬜ TODO | PHASE2-007 |
| PHASE2-011 | Frontend: Live Training Dashboard with WebSocket charts | ⬜ TODO | PHASE2-010 |
| PHASE2-012 | Frontend: Experiment Tracker UI | ⬜ TODO | PHASE2-009 |
| PHASE2-013 | Frontend: Methodology Selector wizard | ⬜ TODO | PHASE1 complete |
| PHASE2-014 | Frontend: GPU Selector page | ⬜ TODO | PHASE1 complete |
| PHASE2-015 | Frontend: Cost Estimator page | ⬜ TODO | PHASE1 complete |

## PHASE 3 — Cloud, Evaluation & Deploy (Weeks 9–12)

| ID | Task | Status | Depends On |
|----|------|--------|------------|
| PHASE3-001 | GPU pricing service — RunPod + Lambda Labs API integration | ⬜ TODO | PHASE2 complete |
| PHASE3-002 | GPU pricing Redis cache with TTL | ⬜ TODO | PHASE3-001 |
| PHASE3-003 | Cost forecaster service — pre-flight cost calculation | ⬜ TODO | PHASE3-001 |
| PHASE3-004 | Cloud launcher — submit jobs to RunPod via API | ⬜ TODO | PHASE3-001 |
| PHASE3-005 | training_engine/evaluation/benchmark.py — MMLU/HellaSwag/ARC | ⬜ TODO | PHASE2 complete |
| PHASE3-006 | training_engine/evaluation/compare.py — base vs fine-tuned | ⬜ TODO | PHASE2 complete |
| PHASE3-007 | Frontend: Evaluation Playground — side-by-side comparison | ⬜ TODO | PHASE3-006 |
| PHASE3-008 | training_engine/export/merge_lora.py | ⬜ TODO | PHASE2 complete |
| PHASE3-009 | training_engine/export/push_hf.py | ⬜ TODO | PHASE3-008 |
| PHASE3-010 | training_engine/export/export_gguf.py | ⬜ TODO | PHASE3-008 |
| PHASE3-011 | Frontend: Deploy & Export Manager page | ⬜ TODO | PHASE3-009 |

## PHASE 4 — Learning Center + Polish (Weeks 13–16)

| ID | Task | Status | Depends On |
|----|------|--------|------------|
| PHASE4-001 | Frontend: Onboarding Wizard — beginner/advanced routing | ⬜ TODO | PHASE3 complete |
| PHASE4-002 | Frontend: Learning Center — conceptual explainers | ⬜ TODO | PHASE4-001 |
| PHASE4-003 | Email notifications — job complete/failed | ⬜ TODO | PHASE3 complete |
| PHASE4-004 | Slack notifications — webhook integration | ⬜ TODO | PHASE4-003 |
| PHASE4-005 | RLHF support — PPOTrainer + RewardTrainer (stretch goal) | ⬜ TODO | PHASE3 complete |
| PHASE4-006 | Production Docker Compose — docker-compose.prod.yml | ⬜ TODO | PHASE4 complete |
| PHASE4-007 | GitHub Actions CI/CD pipeline | ⬜ TODO | PHASE4-006 |
| PHASE4-008 | OrionVexa YouTube demo walkthrough video | ⬜ TODO | PHASE4-006 |

## STATUS KEY
⬜ TODO — not started
🔄 IN PROGRESS — active in CURRENT_TASK.md
✅ DONE — completed and tested
🚫 BLOCKED — waiting on dependency
