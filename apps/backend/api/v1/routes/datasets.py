from uuid import UUID

from core.auth import get_current_user
from core.database import get_db
from fastapi import APIRouter, Depends, File, UploadFile
from models.dataset import Dataset
from models.user import User
from schemas.dataset import DatasetResponse
from services import dataset_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("/upload", response_model=DatasetResponse, status_code=201)
async def upload_dataset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dataset:
    return await dataset_service.upload_dataset(file, current_user, db)


@router.get("", response_model=list[DatasetResponse])
async def list_datasets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Dataset]:
    return await dataset_service.list_datasets(current_user, db)


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dataset:
    return await dataset_service.get_dataset(dataset_id, current_user, db)


@router.post("/{dataset_id}/format", response_model=DatasetResponse)
async def format_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dataset:
    return await dataset_service.format_dataset(dataset_id, current_user, db)


@router.post("/{dataset_id}/quality-check", response_model=DatasetResponse)
async def quality_check_dataset(
    dataset_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dataset:
    return await dataset_service.quality_check_dataset(dataset_id, current_user, db)
