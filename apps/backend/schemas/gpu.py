from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator

from schemas.job import Methodology


class GpuPricingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor: str
    gpu_type: str
    vram_gb: int
    price_per_hour_usd: float


def _check_hours_or_training_params(model: BaseModel) -> None:
    if model.hours is not None:  # type: ignore[attr-defined]
        return
    training_params = (
        model.num_epochs,  # type: ignore[attr-defined]
        model.dataset_row_count,  # type: ignore[attr-defined]
        model.batch_size,  # type: ignore[attr-defined]
        model.gradient_accumulation_steps,  # type: ignore[attr-defined]
    )
    if any(param is None for param in training_params):
        raise ValueError(
            "Provide either `hours`, or all of `num_epochs`, `dataset_row_count`, "
            "`batch_size`, and `gradient_accumulation_steps`."
        )


class CostEstimateRequest(BaseModel):
    vendor: str
    gpu_type: str
    hours: float | None = None
    methodology: Methodology | None = None
    num_epochs: int | None = None
    dataset_row_count: int | None = None
    batch_size: int | None = None
    gradient_accumulation_steps: int | None = None

    @model_validator(mode="after")
    def check_hours_or_training_params(self) -> "CostEstimateRequest":
        _check_hours_or_training_params(self)
        return self


class CostEstimateResponse(BaseModel):
    vendor: str
    gpu_type: str
    price_per_hour_usd: float
    estimated_hours: float
    estimated_cost_usd: float


class CostForecastRequest(BaseModel):
    vendor: str | None = None
    min_vram_gb: int | None = None
    hours: float | None = None
    methodology: Methodology | None = None
    num_epochs: int | None = None
    dataset_row_count: int | None = None
    batch_size: int | None = None
    gradient_accumulation_steps: int | None = None

    @model_validator(mode="after")
    def check_hours_or_training_params(self) -> "CostForecastRequest":
        _check_hours_or_training_params(self)
        return self


class CostForecastOption(BaseModel):
    vendor: str
    gpu_type: str
    vram_gb: int
    price_per_hour_usd: float
    estimated_hours: float
    estimated_cost_usd: float


class CostForecastResponse(BaseModel):
    options: list[CostForecastOption]


class GpuPricingSyncVendorResult(BaseModel):
    status: Literal["ok", "skipped", "failed"]
    offers_fetched: int = 0
    rows_upserted: int = 0
    detail: str | None = None


class GpuPricingSyncResponse(BaseModel):
    vendors: dict[str, GpuPricingSyncVendorResult]
    total_rows_upserted: int
    cached: bool = False
