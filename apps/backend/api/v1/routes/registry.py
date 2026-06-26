from uuid import UUID

from core.auth import get_current_user
from core.database import get_db
from fastapi import APIRouter, Depends, status
from models.model_registry import ModelRegistry
from models.user import User
from schemas.registry import (
    ExportGGUFRequest,
    ModelRegistryCreate,
    ModelRegistryResponse,
    PushHFRequest,
)
from services import registry_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("", response_model=list[ModelRegistryResponse])
async def list_registry(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ModelRegistry]:
    return await registry_service.list_registry(current_user, db)


@router.post("", response_model=ModelRegistryResponse, status_code=status.HTTP_201_CREATED)
async def create_registry_entry(
    payload: ModelRegistryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModelRegistry:
    return await registry_service.create_registry_entry(payload, current_user, db)


@router.get("/{entry_id}", response_model=ModelRegistryResponse)
async def get_registry_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModelRegistry:
    return await registry_service.get_registry_entry(entry_id, current_user, db)


@router.post("/{entry_id}/push-hf", response_model=ModelRegistryResponse)
async def push_to_hf(
    entry_id: UUID,
    payload: PushHFRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModelRegistry:
    return await registry_service.push_to_hf(entry_id, payload, current_user, db)


@router.post("/{entry_id}/export-gguf", response_model=ModelRegistryResponse)
async def export_to_gguf(
    entry_id: UUID,
    payload: ExportGGUFRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModelRegistry:
    return await registry_service.export_to_gguf(entry_id, payload, current_user, db)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_registry_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await registry_service.delete_registry_entry(entry_id, current_user, db)
