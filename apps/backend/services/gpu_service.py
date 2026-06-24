import math

from core.exceptions import NotFoundError
from models.gpu_pricing import GpuPricing
from schemas.gpu import CostEstimateRequest, CostEstimateResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Heuristic average wall-clock seconds per optimizer step, by methodology — used only when
# an estimate is requested from training params (no real benchmark data available yet).
# LoRA/QLoRA are cheaper per step than full-weight SFT; DPO/ORPO/RLHF carry the extra cost of
# a second forward pass (reference/reward model). Revisit once PHASE3-001's real GPU
# benchmarking lands.
SECONDS_PER_STEP_BY_METHODOLOGY: dict[str, float] = {
    "sft": 3.0,
    "lora": 1.8,
    "qlora": 2.2,
    "dpo": 3.5,
    "orpo": 3.0,
    "rlhf": 6.0,
}
DEFAULT_SECONDS_PER_STEP = 2.5


async def list_instances(db: AsyncSession, vendor: str | None = None) -> list[GpuPricing]:
    stmt = select(GpuPricing).order_by(GpuPricing.price_per_hour_usd)
    if vendor is not None:
        stmt = stmt.where(GpuPricing.vendor == vendor)
    result = await db.scalars(stmt)
    return list(result)


async def get_pricing(vendor: str, gpu_type: str, db: AsyncSession) -> GpuPricing:
    instance = await db.scalar(
        select(GpuPricing).where(GpuPricing.vendor == vendor, GpuPricing.gpu_type == gpu_type)
    )
    if instance is None:
        raise NotFoundError("No pricing found for that vendor/GPU type.")
    return instance


def _estimate_hours_from_training_params(payload: CostEstimateRequest) -> float:
    assert payload.num_epochs is not None
    assert payload.dataset_row_count is not None
    assert payload.batch_size is not None
    assert payload.gradient_accumulation_steps is not None

    effective_batch_size = payload.batch_size * payload.gradient_accumulation_steps
    total_steps = math.ceil((payload.dataset_row_count * payload.num_epochs) / effective_batch_size)
    seconds_per_step = (
        SECONDS_PER_STEP_BY_METHODOLOGY.get(payload.methodology, DEFAULT_SECONDS_PER_STEP)
        if payload.methodology
        else DEFAULT_SECONDS_PER_STEP
    )
    return (total_steps * seconds_per_step) / 3600


async def estimate_cost(payload: CostEstimateRequest, db: AsyncSession) -> CostEstimateResponse:
    instance = await get_pricing(payload.vendor, payload.gpu_type, db)
    price_per_hour_usd = float(instance.price_per_hour_usd)
    estimated_hours = (
        payload.hours
        if payload.hours is not None
        else _estimate_hours_from_training_params(payload)
    )
    estimated_cost_usd = estimated_hours * price_per_hour_usd
    return CostEstimateResponse(
        vendor=instance.vendor,
        gpu_type=instance.gpu_type,
        price_per_hour_usd=price_per_hour_usd,
        estimated_hours=round(estimated_hours, 4),
        estimated_cost_usd=round(estimated_cost_usd, 2),
    )
