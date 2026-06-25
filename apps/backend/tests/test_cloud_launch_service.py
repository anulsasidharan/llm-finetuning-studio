from uuid import uuid4

import pytest
from core.config import settings
from core.exceptions import ExternalServiceError, ValidationError
from models.fine_tune_job import FineTuneJob
from services import cloud_launch_service
from services.cloud_launchers.base import CloudLauncherError, LaunchedPod
from services.gpu_pricing_providers.base import GpuPricingProviderError


def _job(
    *, cloud_vendor: str | None = "RunPod", gpu_type: str | None = "A10080GBPCIe"
) -> FineTuneJob:
    return FineTuneJob(id=uuid4(), cloud_vendor=cloud_vendor, gpu_type=gpu_type)


@pytest.fixture(autouse=True)
def _configured_settings(monkeypatch):
    monkeypatch.setattr(settings, "RUNPOD_API_KEY", "fake-key")
    monkeypatch.setattr(settings, "TRAINING_ENGINE_DOCKER_IMAGE", "orionvexa/fts-training-engine")


@pytest.mark.asyncio
async def test_launch_job_unsupported_vendor_raises_validation_error():
    with pytest.raises(ValidationError):
        await cloud_launch_service.launch_job(_job(cloud_vendor="AWS"))


@pytest.mark.asyncio
async def test_launch_job_missing_gpu_type_raises_validation_error():
    with pytest.raises(ValidationError):
        await cloud_launch_service.launch_job(_job(gpu_type=None))


@pytest.mark.asyncio
async def test_launch_job_missing_api_key_raises_validation_error(monkeypatch):
    monkeypatch.setattr(settings, "RUNPOD_API_KEY", "")
    with pytest.raises(ValidationError):
        await cloud_launch_service.launch_job(_job())


@pytest.mark.asyncio
async def test_launch_job_missing_docker_image_raises_validation_error(monkeypatch):
    monkeypatch.setattr(settings, "TRAINING_ENGINE_DOCKER_IMAGE", "")
    with pytest.raises(ValidationError):
        await cloud_launch_service.launch_job(_job())


@pytest.mark.asyncio
async def test_launch_job_success(monkeypatch):
    job = _job()
    captured = {}

    async def fake_resolve_gpu_type_id(api_key, gpu_type, client=None):
        captured["resolve_args"] = (api_key, gpu_type)
        return "NVIDIA A100 80GB PCIe"

    async def fake_launch_runpod_pod(**kwargs):
        captured["launch_kwargs"] = kwargs
        return LaunchedPod(pod_id="pod-1", image_name=kwargs["image_name"], machine_id="m-1")

    monkeypatch.setattr(
        cloud_launch_service.runpod_provider, "resolve_gpu_type_id", fake_resolve_gpu_type_id
    )
    monkeypatch.setattr(
        cloud_launch_service.runpod_launcher, "launch_runpod_pod", fake_launch_runpod_pod
    )

    pod = await cloud_launch_service.launch_job(job)

    assert pod.pod_id == "pod-1"
    assert captured["resolve_args"] == ("fake-key", "A10080GBPCIe")
    assert captured["launch_kwargs"]["gpu_type_id"] == "NVIDIA A100 80GB PCIe"
    assert captured["launch_kwargs"]["name"] == f"fts-job-{job.id}"
    assert captured["launch_kwargs"]["env"]["FTS_JOB_ID"] == str(job.id)


@pytest.mark.asyncio
async def test_launch_job_maps_gpu_resolution_failure_to_external_service_error(monkeypatch):
    async def fake_resolve_gpu_type_id(api_key, gpu_type, client=None):
        raise GpuPricingProviderError("no match")

    monkeypatch.setattr(
        cloud_launch_service.runpod_provider, "resolve_gpu_type_id", fake_resolve_gpu_type_id
    )

    with pytest.raises(ExternalServiceError):
        await cloud_launch_service.launch_job(_job())


@pytest.mark.asyncio
async def test_launch_job_maps_launch_failure_to_external_service_error(monkeypatch):
    async def fake_resolve_gpu_type_id(api_key, gpu_type, client=None):
        return "NVIDIA A100 80GB PCIe"

    async def fake_launch_runpod_pod(**kwargs):
        raise CloudLauncherError("no availability")

    monkeypatch.setattr(
        cloud_launch_service.runpod_provider, "resolve_gpu_type_id", fake_resolve_gpu_type_id
    )
    monkeypatch.setattr(
        cloud_launch_service.runpod_launcher, "launch_runpod_pod", fake_launch_runpod_pod
    )

    with pytest.raises(ExternalServiceError):
        await cloud_launch_service.launch_job(_job())
