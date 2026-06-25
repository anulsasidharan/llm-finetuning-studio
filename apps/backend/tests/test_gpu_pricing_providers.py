import httpx
import pytest
from services.gpu_pricing_providers.base import GpuPricingProviderError
from services.gpu_pricing_providers.lambda_labs_provider import fetch_lambda_labs_pricing
from services.gpu_pricing_providers.runpod_provider import fetch_runpod_pricing, resolve_gpu_type_id


def _mock_client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


_RUNPOD_GPU_TYPES_RESPONSE = {
    "data": {
        "gpuTypes": [
            {
                "id": "NVIDIA A100 80GB PCIe",
                "displayName": "NVIDIA A100 80GB PCIe",
                "memoryInGb": 80,
                "securePrice": 1.99,
                "communityPrice": 1.69,
            },
            {
                "id": "NVIDIA GeForce RTX 4090",
                "displayName": "NVIDIA GeForce RTX 4090",
                "memoryInGb": 24,
                "securePrice": None,
                "communityPrice": 0.44,
            },
            {
                # No price at all anywhere - must be skipped.
                "id": "NVIDIA H100 PCIe",
                "displayName": "NVIDIA H100 PCIe",
                "memoryInGb": 80,
                "securePrice": None,
                "communityPrice": None,
            },
        ]
    }
}


@pytest.mark.asyncio
async def test_fetch_runpod_pricing_parses_offers():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer fake-key"
        return httpx.Response(200, json=_RUNPOD_GPU_TYPES_RESPONSE)

    async with _mock_client(handler) as client:
        offers = await fetch_runpod_pricing("fake-key", client=client)

    assert len(offers) == 2
    a100 = next(o for o in offers if o.vram_gb == 80)
    assert a100.vendor == "RunPod"
    assert a100.gpu_type == "A10080GBPCIe"
    assert a100.price_per_hour_usd == 1.99  # securePrice preferred over communityPrice

    rtx = next(o for o in offers if o.vram_gb == 24)
    assert rtx.price_per_hour_usd == 0.44  # falls back to communityPrice


@pytest.mark.asyncio
async def test_fetch_runpod_pricing_raises_on_graphql_errors():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"errors": [{"message": "boom"}]})

    async with _mock_client(handler) as client:
        with pytest.raises(GpuPricingProviderError):
            await fetch_runpod_pricing("fake-key", client=client)


@pytest.mark.asyncio
async def test_fetch_runpod_pricing_raises_on_http_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    async with _mock_client(handler) as client:
        with pytest.raises(GpuPricingProviderError):
            await fetch_runpod_pricing("bad-key", client=client)


@pytest.mark.asyncio
async def test_resolve_gpu_type_id_finds_matching_raw_id():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_RUNPOD_GPU_TYPES_RESPONSE)

    async with _mock_client(handler) as client:
        raw_id = await resolve_gpu_type_id("fake-key", "A10080GBPCIe", client=client)

    assert raw_id == "NVIDIA A100 80GB PCIe"


@pytest.mark.asyncio
async def test_resolve_gpu_type_id_raises_when_no_match():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=_RUNPOD_GPU_TYPES_RESPONSE)

    async with _mock_client(handler) as client:
        with pytest.raises(GpuPricingProviderError):
            await resolve_gpu_type_id("fake-key", "Nonexistent-GPU", client=client)


@pytest.mark.asyncio
async def test_resolve_gpu_type_id_raises_on_http_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    async with _mock_client(handler) as client:
        with pytest.raises(GpuPricingProviderError):
            await resolve_gpu_type_id("bad-key", "A10080GBPCIe", client=client)


@pytest.mark.asyncio
async def test_fetch_lambda_labs_pricing_parses_offers_and_divides_multi_gpu_price():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer fake-key"
        return httpx.Response(
            200,
            json={
                "data": {
                    "gpu_1x_a100": {
                        "instance_type": {
                            "name": "gpu_1x_a100",
                            "price_cents_per_hour": 110,
                            "specs": {"vcpus": 30, "memory_gib": 200, "gpus": 1},
                        }
                    },
                    "gpu_8x_a100_80gb_sxm4": {
                        "instance_type": {
                            "name": "gpu_8x_a100_80gb_sxm4",
                            "price_cents_per_hour": 1432,
                            "specs": {"vcpus": 240, "memory_gib": 1800, "gpus": 8},
                        }
                    },
                    "cpu_4x_general": {
                        "instance_type": {
                            "name": "cpu_4x_general",
                            "price_cents_per_hour": 20,
                            "specs": {"vcpus": 4, "memory_gib": 16, "gpus": 0},
                        }
                    },
                }
            },
        )

    async with _mock_client(handler) as client:
        offers = await fetch_lambda_labs_pricing("fake-key", client=client)

    assert len(offers) == 2
    a100 = next(o for o in offers if o.gpu_type == "A100")
    assert a100.vendor == "Lambda Labs"
    assert a100.vram_gb == 40
    assert a100.price_per_hour_usd == 1.10

    a100_80gb = next(o for o in offers if o.gpu_type == "A100-80GB")
    assert a100_80gb.vram_gb == 80
    assert a100_80gb.price_per_hour_usd == round(14.32 / 8, 4)


@pytest.mark.asyncio
async def test_fetch_lambda_labs_pricing_raises_on_http_error():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"error": {"message": "forbidden"}})

    async with _mock_client(handler) as client:
        with pytest.raises(GpuPricingProviderError):
            await fetch_lambda_labs_pricing("bad-key", client=client)
