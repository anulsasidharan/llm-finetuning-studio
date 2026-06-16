# CONVENTIONS.md — Code Style Rules
# Claude Code must follow these on every file it creates or modifies.

## PYTHON

### Imports order (always)
# 1. stdlib
# 2. third-party
# 3. local (absolute from app root)

### FastAPI route signature (always)
async def route_name(
    param: Type,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ResponseSchema:

### Service method signature (always)
@staticmethod
async def method_name(db: AsyncSession, ...) -> ReturnType:

### Logging (always structlog, never print/logging)
import structlog
log = structlog.get_logger()
log.info("event.name", key=value)   # snake_case event names with dot separator
log.error("event.failed", error=str(e), context=value)

### Exception raising
from core.exceptions import NotFoundError, ValidationError, ConflictError
raise NotFoundError(f"Job {job_id} not found")   # Never raise HTTPException directly in services

### Pydantic models (always v2 style)
from pydantic import BaseModel, Field
model_config = {"from_attributes": True}   # In response schemas

### Async DB queries
result = await db.execute(select(Model).where(Model.id == id))
obj = result.scalar_one_or_none()
if not obj:
    raise NotFoundError(...)

## TYPESCRIPT / REACT

### Import order (always)
// 1. React
// 2. Next.js
// 3. Third-party
// 4. Internal (@/components, @/hooks, @/lib, @/types)

### Component file structure (always)
// 1. Imports
// 2. Types/interfaces
// 3. Component function
// 4. Export

### Types — always explicit, never `any`
interface ExampleProps {
  id: string
  name: string
  onAction: (id: string) => void
}

### API calls — always typed
const data = await api.get<ResponseType>("/api/v1/endpoint").then(r => r.data)

### Error handling in components
if (error) return <ErrorState message="Failed to load data" />
if (isLoading) return <LoadingSpinner />

### Tailwind class order (always use cn() utility)
import { cn } from "@/lib/utils"
className={cn("base-classes", condition && "conditional-classes", className)}

## GIT

### Commit message format (always)
type(scope): description

Types: feat | fix | chore | docs | refactor | test | style
Scopes: backend | frontend | training | infra | docker | db

Examples:
feat(backend): add dataset quality check endpoint
fix(frontend): correct WebSocket reconnection logic
chore(docker): add healthcheck to celery_worker
docs(api): update WebSocket message format spec
refactor(training): extract GPU monitor to separate module
test(backend): add auth endpoint integration tests

### Branch naming
feat/task-id-short-description
fix/task-id-short-description
chore/task-id-short-description

Example: feat/phase1-week2-backend-core

### Never commit
- .env files
- *.bin, *.safetensors, *.gguf, *.pt model weights
- node_modules/, .next/, .venv/
- __pycache__/, *.pyc

## NAMING CONVENTIONS

### Python files: snake_case.py
### Python classes: PascalCase
### Python functions/variables: snake_case
### TypeScript files: kebab-case.tsx or PascalCase.tsx (for components)
### TypeScript components: PascalCase
### TypeScript hooks: camelCase starting with "use"
### TypeScript types/interfaces: PascalCase
### Database tables: snake_case plural (fine_tune_jobs, model_registry)
### Database columns: snake_case
### API routes: kebab-case (/gpu-selector, /cost-estimator)
### Docker containers: fts_{service} (fts_postgres, fts_redis)
### Docker volumes: fts_{name}_data
### Environment variables: SCREAMING_SNAKE_CASE
