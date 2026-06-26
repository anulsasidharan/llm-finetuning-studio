from uuid import UUID

from core.exceptions import NotFoundError
from models.model_registry import ModelRegistry
from models.user import User
from schemas.registry import ExportGGUFRequest, ModelRegistryCreate, PushHFRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tasks.export_tasks import dispatch_export_gguf, dispatch_push_hf


async def list_registry(user: User, db: AsyncSession) -> list[ModelRegistry]:
    result = await db.scalars(
        select(ModelRegistry)
        .where(ModelRegistry.user_id == user.id)
        .order_by(ModelRegistry.created_at.desc())
    )
    return list(result)


async def get_registry_entry(entry_id: UUID, user: User, db: AsyncSession) -> ModelRegistry:
    entry = await db.scalar(
        select(ModelRegistry).where(ModelRegistry.id == entry_id, ModelRegistry.user_id == user.id)
    )
    if entry is None:
        raise NotFoundError("Model registry entry not found.")
    return entry


async def create_registry_entry(
    payload: ModelRegistryCreate, user: User, db: AsyncSession
) -> ModelRegistry:
    entry = ModelRegistry(
        user_id=user.id,
        name=payload.name,
        base_model_id=payload.base_model_id,
        storage_path=payload.storage_path,
        fine_tune_job_id=payload.fine_tune_job_id,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


async def push_to_hf(
    entry_id: UUID, payload: PushHFRequest, user: User, db: AsyncSession
) -> ModelRegistry:
    entry = await get_registry_entry(entry_id, user, db)
    dispatch_push_hf.delay(
        registry_id=str(entry.id),
        storage_path=entry.storage_path or "",
        hf_repo_id=payload.hf_repo_id,
        hf_token=payload.hf_token,
        private=payload.private,
    )
    return entry


async def export_to_gguf(
    entry_id: UUID, payload: ExportGGUFRequest, user: User, db: AsyncSession
) -> ModelRegistry:
    entry = await get_registry_entry(entry_id, user, db)
    dispatch_export_gguf.delay(
        registry_id=str(entry.id),
        storage_path=entry.storage_path or "",
        quantization_type=payload.quantization_type,
    )
    return entry


async def delete_registry_entry(entry_id: UUID, user: User, db: AsyncSession) -> None:
    entry = await get_registry_entry(entry_id, user, db)
    await db.delete(entry)
    await db.commit()
