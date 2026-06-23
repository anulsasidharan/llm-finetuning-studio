from fastapi import APIRouter

from api.v1.routes import auth, datasets, experiments, jobs, models

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
