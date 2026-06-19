import json
from io import BytesIO
from uuid import uuid4

from core.config import settings
from core.exceptions import ValidationError
from core.storage import upload_file
from fastapi import UploadFile
from models.dataset import Dataset
from models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ALLOWED_EXTENSIONS = {".json", ".jsonl"}
ALLOWED_CONTENT_TYPES = {"application/json", "text/plain", "application/octet-stream"}
UNDETECTED_FORMAT = "unknown"


def _validate_upload(filename: str | None, content_type: str | None, size_bytes: int) -> None:
    if not filename or "." not in filename:
        raise ValidationError("Dataset file must have a .json or .jsonl extension.")

    extension = filename[filename.rfind(".") :].lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise ValidationError("Dataset file must have a .json or .jsonl extension.")

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValidationError(f"Unsupported content type: {content_type}.")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise ValidationError(
            f"Dataset file exceeds the {settings.MAX_UPLOAD_SIZE_MB}MB upload limit."
        )


def _count_rows(contents: bytes, filename: str) -> int:
    if filename.lower().endswith(".jsonl"):
        return sum(1 for line in contents.splitlines() if line.strip())

    parsed = json.loads(contents)
    return len(parsed) if isinstance(parsed, list) else 1


async def upload_dataset(file: UploadFile, user: User, db: AsyncSession) -> Dataset:
    contents = await file.read()
    size_bytes = len(contents)
    _validate_upload(file.filename, file.content_type, size_bytes)
    row_count = _count_rows(contents, file.filename)

    object_name = f"{user.id}/{uuid4()}_{file.filename}"
    upload_file(
        settings.BUCKET_DATASETS,
        object_name,
        BytesIO(contents),
        size_bytes,
        file.content_type or "application/octet-stream",
    )

    dataset = Dataset(
        user_id=user.id,
        name=file.filename,
        format=UNDETECTED_FORMAT,
        storage_path=object_name,
        size_bytes=size_bytes,
        row_count=row_count,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    return dataset


async def list_datasets(user: User, db: AsyncSession) -> list[Dataset]:
    result = await db.scalars(
        select(Dataset).where(Dataset.user_id == user.id).order_by(Dataset.created_at.desc())
    )
    return list(result)
