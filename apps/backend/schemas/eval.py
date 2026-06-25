from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

EvalType = Literal["compare", "benchmark"]
EvalJobStatus = Literal["pending", "queued", "running", "completed", "failed"]
Benchmark = Literal["mmlu", "hellaswag", "arc"]


class EvalCompareCreate(BaseModel):
    base_model_id: str
    finetuned_model_id: str
    prompts: list[str] = Field(min_length=1)
    benchmarks: list[Benchmark] | None = None
    max_new_tokens: int = 256
    num_fewshot: int | None = None
    sample_limit: float | None = None


class EvalBenchmarkCreate(BaseModel):
    base_model_id: str
    benchmarks: list[Benchmark] = Field(min_length=1)
    num_fewshot: int | None = None
    sample_limit: float | None = None


class EvalJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    eval_type: EvalType
    status: EvalJobStatus
    base_model_id: str
    finetuned_model_id: str | None
    prompts: list[str] | None
    benchmarks: list[str] | None
    num_fewshot: int | None
    sample_limit: float | None
    max_new_tokens: int | None
    result: dict[str, Any] | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
