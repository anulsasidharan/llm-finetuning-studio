from core.auth import get_current_user
from core.database import get_db
from fastapi import APIRouter, Depends
from models.model_catalog import ModelCatalog
from models.user import User
from schemas.model_catalog import ModelCatalogResponse
from services import model_catalog_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get("/catalog", response_model=list[ModelCatalogResponse])
async def list_catalog(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ModelCatalog]:
    return await model_catalog_service.list_models(db)


@router.get("/catalog/{model_id:path}", response_model=ModelCatalogResponse)
async def get_catalog_model(
    model_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ModelCatalog:
    return await model_catalog_service.get_model(model_id, db)
