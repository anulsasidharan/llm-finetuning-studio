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

## GIT BRANCHING STRATEGY

### Branch hierarchy
main
└── develop
    ├── feat/phase1-week1-001-project-scaffold
    ├── feat/phase1-week2-001-backend-config
    ├── feat/phase1-week2-002-database-setup
    └── fix/phase1-week2-004-migration-error

### Rules (NEVER break these)
- NEVER commit directly to main
- NEVER commit directly to develop
- ALL work happens on feature branches cut from develop
- Feature branches merge INTO develop via PR only
- develop merges INTO main via PR only (at phase milestones)
- main always represents a deployable state

### Feature branch lifecycle
# 1. Always start from latest develop
git checkout develop
git pull origin develop

# 2. Cut feature branch — use task ID from BACKLOG.md
git checkout -b feat/PHASE1-WEEK2-001-backend-config

# 3. Work and commit frequently
git add .
git commit -m "feat(backend): add pydantic-settings config class"

# 4. Push branch
git push -u origin feat/PHASE1-WEEK2-001-backend-config

# 5. Open PR → develop (never → main)
# Use PR template from .github/PULL_REQUEST_TEMPLATE.md

# 6. After PR merged — delete feature branch
git checkout develop
git pull origin develop
git branch -d feat/PHASE1-WEEK2-001-backend-config

### Branch naming convention
feat/{TASK-ID}-{short-description}
fix/{TASK-ID}-{short-description}
chore/{TASK-ID}-{short-description}
refactor/{TASK-ID}-{short-description}
test/{TASK-ID}-{short-description}
docs/{TASK-ID}-{short-description}

Examples:
feat/PHASE1-WEEK2-001-backend-config
feat/PHASE1-WEEK2-005-security-module
fix/PHASE1-WEEK3-001-dataset-upload-cors
chore/PHASE1-WEEK1-002-makefile-setup
test/PHASE2-009-celery-training-task

### Merge strategy
- Feature → develop:  Squash and merge (keeps develop history clean)
- develop → main:     Merge commit (preserves phase milestone marker)

### develop → main promotion trigger
Promote develop to main ONLY when a full phase is complete:
- End of Phase 1 (Week 3 all tasks done)
- End of Phase 2 (Week 8 all tasks done)
- End of Phase 3 (Week 12 all tasks done)
- End of Phase 4 (Week 16 all tasks done)
