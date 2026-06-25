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


async def _fetch_raw_gpu_types(api_key: str, client: httpx.AsyncClient | None = None) -> list[dict]:
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

    return payload.get("data", {}).get("gpuTypes", [])


async def fetch_runpod_pricing(
    api_key: str, client: httpx.AsyncClient | None = None
) -> list[NormalizedGpuOffer]:
    gpu_types = await _fetch_raw_gpu_types(api_key, client)

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


async def resolve_gpu_type_id(
    api_key: str, gpu_type: str, client: httpx.AsyncClient | None = None
) -> str:
    """Reverse-resolves our normalized ``gpu_pricing.gpu_type`` string (e.g.
    "A10080GBPCIe") back to RunPod's own raw GPU type id (e.g.
    "NVIDIA A100 80GB PCIe") — needed because ``fetch_runpod_pricing`` only keeps
    the normalized name for DB storage and discards RunPod's raw ``id``, but the
    cloud launcher's ``podFindAndDeployOnDemand`` mutation requires that exact raw id
    as its ``gpuTypeId`` input.
    """
    gpu_types = await _fetch_raw_gpu_types(api_key, client)

    for gpu in gpu_types:
        vram_gb = gpu.get("memoryInGb")
        display_name = gpu.get("displayName")
        raw_id = gpu.get("id")
        if not vram_gb or not display_name or not raw_id:
            continue
        if _normalize_gpu_type(display_name, round(vram_gb)) == gpu_type:
            return raw_id

    raise GpuPricingProviderError(f"No RunPod GPU type found matching gpu_type={gpu_type!r}.")
