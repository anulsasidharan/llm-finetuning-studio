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
        if self.hours is not None:
            return self
        training_params = (
            self.num_epochs,
            self.dataset_row_count,
            self.batch_size,
            self.gradient_accumulation_steps,
        )
        if any(param is None for param in training_params):
            raise ValueError(
                "Provide either `hours`, or all of `num_epochs`, `dataset_row_count`, "
                "`batch_size`, and `gradient_accumulation_steps`."
            )
        return self


class CostEstimateResponse(BaseModel):
    vendor: str
    gpu_type: str
    price_per_hour_usd: float
    estimated_hours: float
    estimated_cost_usd: float
