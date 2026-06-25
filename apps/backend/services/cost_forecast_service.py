from core.exceptions import NotFoundError
from models.gpu_pricing import GpuPricing
from schemas.gpu import CostForecastOption, CostForecastRequest, CostForecastResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from services.gpu_service import resolve_estimated_hours


async def forecast_cost(payload: CostForecastRequest, db: AsyncSession) -> CostForecastResponse:
    stmt = select(GpuPricing).order_by(GpuPricing.price_per_hour_usd)
    if payload.vendor is not None:
        stmt = stmt.where(GpuPricing.vendor == payload.vendor)
    if payload.min_vram_gb is not None:
        stmt = stmt.where(GpuPricing.vram_gb >= payload.min_vram_gb)

    instances = list(await db.scalars(stmt))
    if not instances:
        raise NotFoundError("No GPU pricing rows match the given filters.")

    estimated_hours = round(resolve_estimated_hours(payload), 4)
    options = [
        CostForecastOption(
            vendor=instance.vendor,
            gpu_type=instance.gpu_type,
            vram_gb=instance.vram_gb,
            price_per_hour_usd=float(instance.price_per_hour_usd),
            estimated_hours=estimated_hours,
            estimated_cost_usd=round(estimated_hours * float(instance.price_per_hour_usd), 2),
        )
        for instance in instances
    ]
    options.sort(key=lambda option: option.estimated_cost_usd)
    return CostForecastResponse(options=options)
