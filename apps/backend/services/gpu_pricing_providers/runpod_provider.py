import re

import httpx

from services.gpu_pricing_providers.base import GpuPricingProviderError, NormalizedGpuOffer

RUNPOD_GRAPHQL_URL = "https://api.runpod.io/graphql"
VENDOR_NAME = "RunPod"

# Confirmed field names against runpod-python's queries/gpus.py (generate_gpu_query) —
# securePrice/communityPrice are real fields on GpuType, just not requested by that
# SDK's own list-all query. securePrice (dedicated, non-interruptible) is preferred
# over communityPrice for training workloads; fall back to communityPrice if unset.
RUNPOD_GPU_TYPES_QUERY = """
query GpuTypes {
  gpuTypes {
    id
    displayName
    memoryInGb
    securePrice
    communityPrice
  }
}
"""

_STRIP_WORDS = re.compile(r"\b(NVIDIA|GeForce)\b", re.IGNORECASE)
_WHITESPACE = re.compile(r"\s+")


def _normalize_gpu_type(display_name: str, vram_gb: int) -> str:
    name = _STRIP_WORDS.sub("", display_name).strip()
    name = _WHITESPACE.sub("", name)
    if str(vram_gb) not in name:
        name = f"{name}-{vram_gb}GB"
    return name


async def fetch_runpod_pricing(
    api_key: str, client: httpx.AsyncClient | None = None
) -> list[NormalizedGpuOffer]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    request_body = {"query": RUNPOD_GPU_TYPES_QUERY}

    owns_client = client is None
    http_client = client or httpx.AsyncClient(timeout=15.0)
    try:
        response = await http_client.post(RUNPOD_GRAPHQL_URL, headers=headers, json=request_body)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise GpuPricingProviderError(f"RunPod API request failed: {exc}") from exc
    finally:
        if owns_client:
            await http_client.aclose()

    payload = response.json()
    if "errors" in payload:
        raise GpuPricingProviderError(f"RunPod GraphQL error: {payload['errors']}")

    gpu_types = payload.get("data", {}).get("gpuTypes", [])
    offers: list[NormalizedGpuOffer] = []
    for gpu in gpu_types:
        vram_gb = gpu.get("memoryInGb")
        price = gpu.get("securePrice") or gpu.get("communityPrice")
        display_name = gpu.get("displayName")
        if not vram_gb or not price or not display_name:
            continue
        offers.append(
            NormalizedGpuOffer(
                vendor=VENDOR_NAME,
                gpu_type=_normalize_gpu_type(display_name, round(vram_gb)),
                vram_gb=round(vram_gb),
                price_per_hour_usd=round(float(price), 4),
            )
        )
    return offers
