import httpx

from services.gpu_pricing_providers.base import GpuPricingProviderError, NormalizedGpuOffer

LAMBDA_LABS_INSTANCE_TYPES_URL = "https://cloud.lambdalabs.com/api/v1/instance-types"
VENDOR_NAME = "Lambda Labs"

# VRAM per GPU, confirmed against skypilot's fetch_lambda_cloud.py (the instance-types
# API itself never reports VRAM, only vcpus/system-memory/gpu count).
GPU_VRAM_GB: dict[str, int] = {
    "A100": 40,
    "A100-80GB": 80,
    "A6000": 48,
    "A10": 24,
    "RTX6000": 24,
    "V100": 16,
    "H100": 80,
    "GH200": 96,
    "B200": 180,
}


def _name_to_gpu(instance_type_name: str) -> str:
    """Instance type names look like 'gpu_{count}x_{gpu_name}_<suffix>'."""
    if instance_type_name == "gpu_8x_a100_80gb_sxm4":
        return "A100-80GB"
    parts = instance_type_name.split("_")
    if len(parts) < 3:
        return ""
    return parts[2].upper()


async def fetch_lambda_labs_pricing(
    api_key: str, client: httpx.AsyncClient | None = None
) -> list[NormalizedGpuOffer]:
    headers = {"Authorization": f"Bearer {api_key}"}

    owns_client = client is None
    http_client = client or httpx.AsyncClient(timeout=15.0)
    try:
        response = await http_client.get(LAMBDA_LABS_INSTANCE_TYPES_URL, headers=headers)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise GpuPricingProviderError(f"Lambda Labs API request failed: {exc}") from exc
    finally:
        if owns_client:
            await http_client.aclose()

    payload = response.json()
    instance_types = payload.get("data", {})

    offers: list[NormalizedGpuOffer] = []
    for instance_name, entry in instance_types.items():
        specs = entry.get("instance_type", {}).get("specs", {})
        gpu_count = specs.get("gpus", 0)
        if not gpu_count:
            continue

        gpu_type = _name_to_gpu(instance_name)
        vram_gb = GPU_VRAM_GB.get(gpu_type)
        if vram_gb is None:
            continue

        price_cents_per_hour = entry.get("instance_type", {}).get("price_cents_per_hour")
        if not price_cents_per_hour:
            continue
        price_per_gpu_usd = (price_cents_per_hour / 100) / gpu_count

        offers.append(
            NormalizedGpuOffer(
                vendor=VENDOR_NAME,
                gpu_type=gpu_type,
                vram_gb=vram_gb,
                price_per_hour_usd=round(price_per_gpu_usd, 4),
            )
        )
    return offers
