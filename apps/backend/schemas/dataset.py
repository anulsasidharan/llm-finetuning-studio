from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

DatasetFormat = Literal["alpaca", "sharegpt", "chatml", "unknown"]


class DatasetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    format: DatasetFormat
    storage_path: str
    size_bytes: int
    row_count: int
    quality_report: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
