from core.auth import get_current_user
from core.database import get_db
from fastapi import APIRouter, Depends, Query
from models.gpu_pricing import GpuPricing
from models.user import User
from schemas.gpu import CostEstimateRequest, CostEstimateResponse, GpuPricingResponse
from services import gpu_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/instances", response_model=list[GpuPricingResponse])
async def list_instances(
    vendor: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[GpuPricing]:
    return await gpu_service.list_instances(db, vendor=vendor)


@router.get("/pricing", response_model=GpuPricingResponse)
async def get_pricing(
    vendor: str = Query(...),
    gpu_type: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> GpuPricing:
    return await gpu_service.get_pricing(vendor, gpu_type, db)


@router.post("/estimate", response_model=CostEstimateResponse)
async def estimate_cost(
    payload: CostEstimateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CostEstimateResponse:
    return await gpu_service.estimate_cost(payload, db)
