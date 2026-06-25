from uuid import UUID

from core.auth import get_current_user
from core.database import get_db
from fastapi import APIRouter, Depends
from models.eval_job import EvalJob
from models.user import User
from schemas.eval import EvalBenchmarkCreate, EvalCompareCreate, EvalJobResponse
from services import eval_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/compare", response_model=EvalJobResponse, status_code=201)
async def create_compare_job(
    payload: EvalCompareCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvalJob:
    return await eval_service.create_compare_job(payload, current_user, db)


@router.post("/benchmark", response_model=EvalJobResponse, status_code=201)
async def create_benchmark_job(
    payload: EvalBenchmarkCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvalJob:
    return await eval_service.create_benchmark_job(payload, current_user, db)


@router.get("", response_model=list[EvalJobResponse])
async def list_eval_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[EvalJob]:
    return await eval_service.list_eval_jobs(current_user, db)


@router.get("/{eval_id}", response_model=EvalJobResponse)
async def get_eval_job(
    eval_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> EvalJob:
    return await eval_service.get_eval_job(eval_id, current_user, db)
