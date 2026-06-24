from uuid import UUID

from pydantic import BaseModel, ConfigDict


class GpuPricingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    vendor: str
    gpu_type: str
    vram_gb: int
    price_per_hour_usd: float
