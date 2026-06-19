from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    format: str
    storage_path: str
    size_bytes: int
    row_count: int
    quality_report: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
