from uuid import UUID

from core.exceptions import NotFoundError, ValidationError
from models.fine_tune_job import FineTuneJob
from models.user import User
from schemas.job import FineTuneJobCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tasks.training_tasks import dispatch_training_job

from services import cloud_launch_service
from services.cloud_launchers.base import LaunchedPod
from services.dataset_service import get_dataset

JOB_STATUS_PENDING = "pending"

COMMON_REQUIRED_KEYS = {"learning_rate", "num_epochs", "batch_size"}

METHOD_SPECIFIC_REQUIRED_KEYS: dict[str, set[str]] = {
    "sft": set(),
    "lora": {"lora_r", "lora_alpha"},
    "qlora": {"lora_r", "lora_alpha"},
    "dpo": {"beta"},
    "orpo": {"beta"},
    "rlhf": {"reward_model_id"},
}

SUPPORTED_METHODOLOGIES = set(METHOD_SPECIFIC_REQUIRED_KEYS)


def _validate_training_config(methodology: str, training_config: dict) -> None:
    required_keys = COMMON_REQUIRED_KEYS | METHOD_SPECIFIC_REQUIRED_KEYS[methodology]
    missing_keys = required_keys - training_config.keys()
    if missing_keys:
        raise ValidationError(
            f"training_config is missing required keys for {methodology}: "
            f"{sorted(missing_keys)}"
        )


async def create_job(payload: FineTuneJobCreate, user: User, db: AsyncSession) -> FineTuneJob:
    if payload.methodology not in SUPPORTED_METHODOLOGIES:
        raise ValidationError(
            f"Unsupported methodology: {payload.methodology}. "
            f"Must be one of {sorted(SUPPORTED_METHODOLOGIES)}."
        )
    _validate_training_config(payload.methodology, payload.training_config)

    dataset = None
    if payload.dataset_id is not None:
        dataset = await get_dataset(payload.dataset_id, user, db)

    job = FineTuneJob(
        user_id=user.id,
        dataset_id=payload.dataset_id,
        status=JOB_STATUS_PENDING,
        base_model_id=payload.base_model_id,
        methodology=payload.methodology,
        training_config=payload.training_config,
        gpu_type=payload.gpu_type,
        cloud_vendor=payload.cloud_vendor,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    dispatch_training_job.delay(
        job_id=str(job.id),
        base_model_id=job.base_model_id,
        methodology=job.methodology,
        training_config=job.training_config,
        dataset_storage_path=dataset.storage_path if dataset else None,
        dataset_format=dataset.format if dataset else None,
    )

    return job


async def list_jobs(user: User, db: AsyncSession) -> list[FineTuneJob]:
    result = await db.scalars(
        select(FineTuneJob)
        .where(FineTuneJob.user_id == user.id)
        .order_by(FineTuneJob.created_at.desc())
    )
    return list(result)


async def get_job(job_id: UUID, user: User, db: AsyncSession) -> FineTuneJob:
    job = await db.scalar(
        select(FineTuneJob).where(FineTuneJob.id == job_id, FineTuneJob.user_id == user.id)
    )
    if job is None:
        raise NotFoundError("Fine-tune job not found.")
    return job


async def launch_cloud_job(job_id: UUID, user: User, db: AsyncSession) -> LaunchedPod:
    job = await get_job(job_id, user, db)
    return await cloud_launch_service.launch_job(job)
