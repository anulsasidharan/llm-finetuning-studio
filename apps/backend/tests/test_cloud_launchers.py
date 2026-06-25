import json

import httpx
import pytest
from services.cloud_launchers.base import CloudLauncherError
from services.cloud_launchers.runpod_launcher import launch_runpod_pod, terminate_runpod_pod


def _mock_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.asyncio
async def test_launch_runpod_pod_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer fake-key"
        body = json.loads(request.content)["query"]
        assert "podFindAndDeployOnDemand" in body
        assert "NVIDIA A100 80GB PCIe" in body
        assert "fts-job-123" in body
        assert '{ key: "FTS_JOB_ID", value: "123" }' in body
        return httpx.Response(
            200,
            json={
                "data": {
                    "podFindAndDeployOnDemand": {
                        "id": "pod-abc123",
                        "imageName": "orionvexa/fts-training-engine:latest",
                        "machineId": "machine-xyz",
                    }
                }
            },
        )

    async with _mock_client(handler) as client:
        pod = await launch_runpod_pod(
            api_key="fake-key",
            name="fts-job-123",
            image_name="orionvexa/fts-training-engine:latest",
            gpu_type_id="NVIDIA A100 80GB PCIe",
            env={"FTS_JOB_ID": "123"},
            client=client,
        )

    assert pod.pod_id == "pod-abc123"
    assert pod.image_name == "orionvexa/fts-training-engine:latest"
    assert pod.machine_id == "machine-xyz"


@pytest.mark.asyncio
async def test_launch_runpod_pod_raises_when_no_pod_returned():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": {"podFindAndDeployOnDemand": None}})

    async with _mock_client(handler) as client:
        with pytest.raises(CloudLauncherError):
            await launch_runpod_pod(
                api_key="fake-key",
                name="fts-job-123",
                image_name="image",
                gpu_type_id="NVIDIA A100 80GB PCIe",
                env={},
                client=client,
            )


@pytest.mark.asyncio
async def test_launch_runpod_pod_raises_on_graphql_errors():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "boom"}]})

    async with _mock_client(handler) as client:
        with pytest.raises(CloudLauncherError):
            await launch_runpod_pod(
                api_key="fake-key",
                name="fts-job-123",
                image_name="image",
                gpu_type_id="NVIDIA A100 80GB PCIe",
                env={},
                client=client,
            )


@pytest.mark.asyncio
async def test_launch_runpod_pod_raises_on_http_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    async with _mock_client(handler) as client:
        with pytest.raises(CloudLauncherError):
            await launch_runpod_pod(
                api_key="bad-key",
                name="fts-job-123",
                image_name="image",
                gpu_type_id="NVIDIA A100 80GB PCIe",
                env={},
                client=client,
            )


@pytest.mark.asyncio
async def test_terminate_runpod_pod_success():
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.content.decode()
        assert "podTerminate" in body
        assert "pod-abc123" in body
        return httpx.Response(200, json={"data": {"podTerminate": None}})

    async with _mock_client(handler) as client:
        await terminate_runpod_pod(api_key="fake-key", pod_id="pod-abc123", client=client)


@pytest.mark.asyncio
async def test_terminate_runpod_pod_raises_on_graphql_errors():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "pod not found"}]})

    async with _mock_client(handler) as client:
        with pytest.raises(CloudLauncherError):
            await terminate_runpod_pod(api_key="fake-key", pod_id="missing-pod", client=client)
