from core.config import settings
from core.exceptions import ExternalServiceError, ValidationError
from models.fine_tune_job import FineTuneJob

from services.cloud_launchers import runpod_launcher
from services.cloud_launchers.base import CloudLauncherError, LaunchedPod
from services.gpu_pricing_providers import runpod_provider
from services.gpu_pricing_providers.base import GpuPricingProviderError

# Only RunPod has a real launch-API integration so far (Lambda Labs/AWS/GCP/Azure only
# have pricing data, per PHASE3-001) — mirrors the rest of this codebase's pattern of
# adding cloud-vendor support one at a time rather than stubbing every vendor up front.
SUPPORTED_CLOUD_VENDORS = frozenset({"RunPod"})


def _build_worker_env(job_id: str) -> dict[str, str]:
    """Env vars the launched pod's training_engine Celery worker needs to reach this
    deployment's own Postgres/Redis/MinIO and join the "gpu_training" queue exactly like
    the local worker in docker-compose.gpu.yml does — same env_file: .env vars plus the
    CUDA_VISIBLE_DEVICES override that compose file sets explicitly.
    """
    return {
        "DATABASE_URL_SYNC": settings.DATABASE_URL_SYNC,
        "REDIS_URL": settings.REDIS_URL,
        "CELERY_BROKER_URL": settings.CELERY_BROKER_URL,
        "CELERY_RESULT_BACKEND": settings.CELERY_RESULT_BACKEND,
        "TRAINING_ENGINE_REDIS_URL": settings.TRAINING_ENGINE_REDIS_URL,
        "MINIO_HOST": settings.MINIO_HOST,
        "MINIO_PORT": str(settings.MINIO_PORT),
        "MINIO_ROOT_USER": settings.MINIO_ROOT_USER,
        "MINIO_ROOT_PASSWORD": settings.MINIO_ROOT_PASSWORD,
        "MINIO_USE_SSL": str(settings.MINIO_USE_SSL).lower(),
        "CUDA_VISIBLE_DEVICES": "0",
        "FTS_JOB_ID": job_id,
    }


async def launch_job(job: FineTuneJob) -> LaunchedPod:
    if job.cloud_vendor not in SUPPORTED_CLOUD_VENDORS:
        raise ValidationError(
            f"Cloud launch is not supported for cloud_vendor={job.cloud_vendor!r}. "
            f"Supported vendors: {sorted(SUPPORTED_CLOUD_VENDORS)}."
        )
    if not job.gpu_type:
        raise ValidationError("Job has no gpu_type set — cannot resolve a cloud GPU to launch.")
    if not settings.RUNPOD_API_KEY:
        raise ValidationError("RUNPOD_API_KEY is not configured.")
    if not settings.TRAINING_ENGINE_DOCKER_IMAGE:
        raise ValidationError("TRAINING_ENGINE_DOCKER_IMAGE is not configured.")

    try:
        gpu_type_id = await runpod_provider.resolve_gpu_type_id(
            settings.RUNPOD_API_KEY, job.gpu_type
        )
    except GpuPricingProviderError as exc:
        raise ExternalServiceError(f"Could not resolve RunPod GPU type: {exc}") from exc

    try:
        return await runpod_launcher.launch_runpod_pod(
            api_key=settings.RUNPOD_API_KEY,
            name=f"fts-job-{job.id}",
            image_name=settings.TRAINING_ENGINE_DOCKER_IMAGE,
            gpu_type_id=gpu_type_id,
            env=_build_worker_env(str(job.id)),
        )
    except CloudLauncherError as exc:
        raise ExternalServiceError(f"RunPod pod launch failed: {exc}") from exc
