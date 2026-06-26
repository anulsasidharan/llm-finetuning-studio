from fastapi import APIRouter

from api.v1.routes import auth, datasets, eval, experiments, gpu, jobs, models, registry

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["datasets"])
api_router.include_router(eval.router, prefix="/eval", tags=["eval"])
api_router.include_router(experiments.router, prefix="/experiments", tags=["experiments"])
api_router.include_router(gpu.router, prefix="/gpu", tags=["gpu"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(registry.router, prefix="/registry", tags=["registry"])
