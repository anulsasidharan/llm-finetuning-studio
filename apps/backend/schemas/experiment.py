from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from schemas.job import JobStatus, Methodology


class ExperimentCreate(BaseModel):
    name: str
    description: str | None = None


class ExperimentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class ExperimentRunCreate(BaseModel):
    fine_tune_job_id: UUID


class ExperimentRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: UUID
    fine_tune_job_id: UUID
    metrics: dict[str, Any] | None
    created_at: datetime


class ExperimentRunCompareEntry(BaseModel):
    run_id: UUID
    fine_tune_job_id: UUID
    base_model_id: str
    methodology: Methodology
    status: JobStatus
    training_config: dict[str, Any]
    metrics: dict[str, Any] | None
    created_at: datetime


class ExperimentCompareResponse(BaseModel):
    experiment_id: UUID
    runs: list[ExperimentRunCompareEntry]
    metrics_by_name: dict[str, list[dict[str, Any]]]
