# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE3-011
## TASK NAME: Frontend: Deploy & Export Manager page
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 3, Week 9
## BRANCH: feat/PHASE3-011-deploy-export-manager

## NEXT TASK
PHASE4-001 (Frontend: Onboarding Wizard) — first task of Phase 4.

## SUMMARY (this session, 2026-06-25)
Built the full Deploy & Export Manager feature — backend registry CRUD + export
dispatch plumbing + frontend page — completing Phase 3.

**Backend files created:**
- `apps/backend/schemas/registry.py` — ModelRegistryResponse, ModelRegistryCreate,
  PushHFRequest, ExportGGUFRequest (with QuantizationType Literal of 10 quant types)
- `apps/backend/services/registry_service.py` — list/get/create/push_hf/export_gguf/delete,
  all async SQLAlchemy, raises NotFoundError on missing entries
- `apps/backend/tasks/export_tasks.py` — dispatch_push_hf + dispatch_export_gguf
  Celery tasks; follow eval_tasks.py pattern: lightweight backend tasks that call
  celery.send_task("training_engine.tasks.run_export_job", queue="gpu_training")
- `apps/backend/api/v1/routes/registry.py` — GET/POST /registry, GET/POST/DELETE
  /registry/{id}, POST /registry/{id}/push-hf, POST /registry/{id}/export-gguf
- Updated `apps/backend/api/v1/__init__.py` to register registry router

**Frontend files created:**
- Regenerated `apps/frontend/openapi/schema.json` + `types/api-schema.d.ts`
- Updated `apps/frontend/types/index.ts` — 4 new registry type exports
- `apps/frontend/hooks/useRegistry.ts` — 6 hooks: useRegistryEntries, useRegistryEntry,
  useCreateRegistryEntry, usePushToHF, useExportToGGUF, useDeleteRegistryEntry
- `apps/frontend/app/(dashboard)/deploy/page.tsx` — table of registered models; 4
  dialog components (Register, PushHF, ExportGGUF, Delete); export status badges
  showing hf_repo_id / gguf_export_path state

**Verification:**
- `npm run build` — passes (TypeScript clean, /deploy in route list)
- `ruff check` + `ruff format --check` — all backend files pass
- All pre-commit hooks passed on commit

## GOTCHAS LOGGED
- `training_engine.tasks.run_export_job` task does NOT exist yet in training_engine/tasks.py
  — the dispatch_push_hf / dispatch_export_gguf Celery tasks call it via celery.send_task
  (fire-and-forget to the gpu_training queue). A future task would need to implement
  run_export_job in training_engine using the existing export/push_hf.py and
  export/export_gguf.py modules.
- Registry entry status is inferred from field values (hf_repo_id / gguf_export_path
  populated = done, null = not exported) — no separate status column in model_registry.
  Export operations are fire-and-forget from the API layer; the frontend reflects the
  last-known persisted state.
