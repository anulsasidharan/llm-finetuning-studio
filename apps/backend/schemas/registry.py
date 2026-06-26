from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

QuantizationType = Literal[
    "f32", "f16", "q8_0", "q6_k", "q5_k_m", "q5_0", "q4_k_m", "q4_0", "q3_k_m", "q2_k"
]


class ModelRegistryCreate(BaseModel):
    name: str
    base_model_id: str
    storage_path: str | None = None
    fine_tune_job_id: UUID | None = None


class ModelRegistryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    fine_tune_job_id: UUID | None
    name: str
    base_model_id: str
    storage_path: str | None
    hf_repo_id: str | None
    gguf_export_path: str | None
    vllm_endpoint: str | None
    created_at: datetime
    updated_at: datetime


class PushHFRequest(BaseModel):
    hf_repo_id: str
    hf_token: str
    private: bool = True


class ExportGGUFRequest(BaseModel):
    quantization_type: QuantizationType = "q4_k_m"
