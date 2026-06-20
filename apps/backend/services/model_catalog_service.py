from core.exceptions import NotFoundError
from models.model_catalog import ModelCatalog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def list_models(db: AsyncSession) -> list[ModelCatalog]:
    result = await db.scalars(select(ModelCatalog).order_by(ModelCatalog.display_name))
    return list(result)


async def get_model(model_id: str, db: AsyncSession) -> ModelCatalog:
    model = await db.scalar(select(ModelCatalog).where(ModelCatalog.model_id == model_id))
    if model is None:
        raise NotFoundError("Model not found in catalog.")
    return model
