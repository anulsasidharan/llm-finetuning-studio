from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

Methodology = Literal["sft", "lora", "qlora", "dpo", "orpo", "rlhf"]
JobStatus = Literal["pending", "queued", "running", "completed", "failed", "cancelled"]


class FineTuneJobCreate(BaseModel):
    base_model_id: str
    methodology: Methodology
    training_config: dict[str, Any]
    dataset_id: UUID | None = None
    gpu_type: str | None = None
    cloud_vendor: str | None = None


class FineTuneJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    dataset_id: UUID | None
    status: JobStatus
    base_model_id: str
    methodology: Methodology
    training_config: dict[str, Any]
    gpu_type: str | None
    cloud_vendor: str | None
    train_loss: float | None
    eval_loss: float | None
    gpu_utilization_pct: float | None
    vram_used_gb: float | None
    tokens_per_second: float | None
    estimated_cost_usd: float | None
    actual_cost_usd: float | None
    created_at: datetime
    updated_at: datetime


class FineTuneJobConfigResponse(BaseModel):
    training_config: dict[str, Any]
