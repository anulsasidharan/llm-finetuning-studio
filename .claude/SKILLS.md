# SKILLS.md — How Claude Code Should Work on This Project
# Reusable patterns and rules for every task in this codebase.

## BEFORE STARTING ANY TASK
1. Read .claude/MEMORY.md — restore current phase and last state
2. Read .claude/tasks/CURRENT_TASK.md — understand exactly what to build
3. Check if relevant files already exist before creating new ones
4. Never modify docker-compose.yml, .env.example, or CLAUDE.md without explicit instruction

## PYTHON SKILLS

### Create a FastAPI route
```python
# apps/backend/api/v1/routes/example.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from core.database import get_db
from core.auth import get_current_user
from models.user import User
from schemas.example import ExampleCreate, ExampleResponse
from services.example_service import ExampleService

router = APIRouter(prefix="/examples", tags=["examples"])

@router.get("/", response_model=list[ExampleResponse])
async def list_examples(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ExampleService.list(db, user_id=current_user.id)
```

### Create a SQLAlchemy model
```python
# apps/backend/models/example.py
import uuid
from datetime import datetime
from sqlalchemy import String, Text, Boolean, TIMESTAMP, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from core.database import Base

class Example(Base):
    __tablename__ = "examples"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())
```

### Create a Pydantic schema
```python
# apps/backend/schemas/example.py
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class ExampleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)

class ExampleCreate(ExampleBase):
    pass

class ExampleResponse(ExampleBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
```

### Create a service layer
```python
# apps/backend/services/example_service.py
import structlog
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.example import Example
from schemas.example import ExampleCreate
from core.exceptions import NotFoundError

log = structlog.get_logger()

class ExampleService:
    @staticmethod
    async def list(db: AsyncSession, user_id: UUID) -> list[Example]:
        result = await db.execute(select(Example).where(Example.user_id == user_id))
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, user_id: UUID, data: ExampleCreate) -> Example:
        obj = Example(user_id=user_id, **data.model_dump())
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        log.info("example.created", id=str(obj.id))
        return obj
```

### Run a Celery task
```python
# apps/backend/tasks/training_tasks.py
from core.celery_app import celery_app
import structlog

log = structlog.get_logger()

@celery_app.task(bind=True, queue="training", max_retries=3)
def run_training_job(self, job_id: str, config: dict):
    log.info("training.started", job_id=job_id)
    try:
        # Call training engine
        pass
    except Exception as exc:
        log.error("training.failed", job_id=job_id, error=str(exc))
        raise self.retry(exc=exc, countdown=60)
```

### After adding a new model — always create migration
```bash
docker compose run --rm backend alembic revision --autogenerate -m "add example table"
docker compose run --rm backend alembic upgrade head
```

## TYPESCRIPT / REACT SKILLS

### Create a page component (App Router)
```tsx
// apps/frontend/app/(dashboard)/example/page.tsx
import { Suspense } from "react"
import { PageContainer } from "@/components/layout/PageContainer"
import { ExampleList } from "@/components/example/ExampleList"
import { LoadingSpinner } from "@/components/shared/LoadingSpinner"

export const metadata = { title: "Example | LLM Fine-Tuning Studio" }

export default function ExamplePage() {
  return (
    <PageContainer title="Example" subtitle="Description here">
      <Suspense fallback={<LoadingSpinner />}>
        <ExampleList />
      </Suspense>
    </PageContainer>
  )
}
```

### Create a client component with API call
```tsx
// apps/frontend/components/example/ExampleList.tsx
"use client"
import { useQuery } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Example } from "@/types"

export function ExampleList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["examples"],
    queryFn: () => api.get<Example[]>("/api/v1/examples").then(r => r.data),
  })

  if (isLoading) return <div>Loading...</div>
  if (error) return <div>Error loading examples</div>
  return <ul>{data?.map(e => <li key={e.id}>{e.name}</li>)}</ul>
}
```

### Create a custom hook
```tsx
// apps/frontend/hooks/useExample.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "@/lib/api"
import type { Example, ExampleCreate } from "@/types"

export function useExamples() {
  return useQuery({
    queryKey: ["examples"],
    queryFn: () => api.get<Example[]>("/api/v1/examples").then(r => r.data),
  })
}

export function useCreateExample() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: ExampleCreate) =>
      api.post<Example>("/api/v1/examples", data).then(r => r.data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["examples"] }),
  })
}
```

### WebSocket connection pattern
```tsx
// Only for the Training Dashboard — do not use WebSocket elsewhere
import { useEffect, useRef, useState } from "react"

export function useTrainingWebSocket(jobId: string) {
  const ws = useRef<WebSocket | null>(null)
  const [metrics, setMetrics] = useState<any[]>([])

  useEffect(() => {
    if (!jobId) return
    ws.current = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL}/ws/training/${jobId}`)
    ws.current.onmessage = (e) => {
      const data = JSON.parse(e.data)
      if (data.type === "metrics_update") {
        setMetrics(prev => [...prev.slice(-500), data])
      }
    }
    return () => ws.current?.close()
  }, [jobId])

  return { metrics }
}
```

## DOCKER SKILLS

### Check service health
```bash
docker compose ps                          # All containers status
docker compose logs -f backend             # Backend logs
docker exec -it fts_postgres psql -U fts_user -d fts_db   # Postgres shell
docker exec -it fts_redis redis-cli -a $REDIS_PASSWORD     # Redis CLI
```

### Restart a single service
```bash
docker compose restart backend
docker compose up -d --build backend       # Rebuild and restart
```

### Reset everything
```bash
docker compose down -v && docker compose up -d
```

## RULES — NEVER BREAK THESE
- Never use `os.environ.get()` directly — always use Settings class
- Never write sync SQLAlchemy sessions in async routes
- Never store model binary files (.bin, .safetensors, .gguf) in the git repo
- Never hardcode GPU prices — always read from Redis cache (key: gpu:pricing)
- Never skip Alembic migration when adding/changing a DB model
- Never use relative imports in backend (../../) — always absolute from app root
- Never call fetch() directly in React components — always use the typed api client
- Never add "use client" to a page.tsx unless absolutely necessary
- Never create a new Docker network — always use fts_network
