from core.exceptions import NotFoundError
from models.gpu_pricing import GpuPricing
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


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
