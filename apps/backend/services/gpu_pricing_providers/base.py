from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizedGpuOffer:
    vendor: str
    gpu_type: str
    vram_gb: int
    price_per_hour_usd: float


class GpuPricingProviderError(Exception):
    """Raised when a live GPU pricing provider's API call fails or returns an
    unexpected shape. Callers (gpu_pricing_sync_service) catch this per-vendor
    so one provider outage doesn't block the other vendor's sync."""
