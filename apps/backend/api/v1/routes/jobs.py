from uuid import UUID

from core.auth import get_current_user
from core.database import get_db
from fastapi import APIRouter, Depends
from models.fine_tune_job import FineTuneJob
from models.user import User
from schemas.job import (
    CloudLaunchResponse,
    FineTuneJobConfigResponse,
    FineTuneJobCreate,
    FineTuneJobResponse,
)
from services import job_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("", response_model=FineTuneJobResponse, status_code=201)
async def create_job(
    payload: FineTuneJobCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FineTuneJob:
    return await job_service.create_job(payload, current_user, db)


@router.get("", response_model=list[FineTuneJobResponse])
async def list_jobs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FineTuneJob]:
    return await job_service.list_jobs(current_user, db)


@router.get("/{job_id}", response_model=FineTuneJobResponse)
async def get_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FineTuneJob:
    return await job_service.get_job(job_id, current_user, db)


@router.get("/{job_id}/config", response_model=FineTuneJobConfigResponse)
async def get_job_config(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FineTuneJob:
    return await job_service.get_job(job_id, current_user, db)


@router.post("/{job_id}/launch-cloud", response_model=CloudLaunchResponse)
async def launch_cloud_job(
    job_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CloudLaunchResponse:
    pod = await job_service.launch_cloud_job(job_id, current_user, db)
    return CloudLaunchResponse(
        pod_id=pod.pod_id, image_name=pod.image_name, machine_id=pod.machine_id
    )
