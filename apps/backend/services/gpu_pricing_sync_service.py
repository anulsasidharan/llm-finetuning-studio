import structlog
from core.config import settings
from models.gpu_pricing import GpuPricing
from schemas.gpu import GpuPricingSyncResponse, GpuPricingSyncVendorResult
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from services.gpu_pricing_providers import lambda_labs_provider, runpod_provider
from services.gpu_pricing_providers.base import GpuPricingProviderError, NormalizedGpuOffer

log = structlog.get_logger()

# vendor key -> (api_key, fetch_fn) — keys match the `vendors` dict in GpuPricingSyncResponse.
# fetch_fn is a thunk (not a direct function reference) so tests can monkeypatch
# runpod_provider.fetch_runpod_pricing / lambda_labs_provider.fetch_lambda_labs_pricing and have
# the new function picked up at call time instead of the one captured when this module loaded.
_PROVIDERS = {
    "runpod": (
        lambda: settings.RUNPOD_API_KEY,
        lambda api_key: runpod_provider.fetch_runpod_pricing(api_key),
    ),
    "lambda_labs": (
        lambda: settings.LAMBDA_LABS_API_KEY,
        lambda api_key: lambda_labs_provider.fetch_lambda_labs_pricing(api_key),
    ),
}


def _dedupe_cheapest(offers: list[NormalizedGpuOffer]) -> list[NormalizedGpuOffer]:
    cheapest: dict[tuple[str, str], NormalizedGpuOffer] = {}
    for offer in offers:
        key = (offer.vendor, offer.gpu_type)
        existing = cheapest.get(key)
        if existing is None or offer.price_per_hour_usd < existing.price_per_hour_usd:
            cheapest[key] = offer
    return list(cheapest.values())


async def _upsert_offers(db: AsyncSession, offers: list[NormalizedGpuOffer]) -> int:
    if not offers:
        return 0
    values = [
        {
            "vendor": offer.vendor,
            "gpu_type": offer.gpu_type,
            "vram_gb": offer.vram_gb,
            "price_per_hour_usd": offer.price_per_hour_usd,
        }
        for offer in offers
    ]
    stmt = insert(GpuPricing).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["vendor", "gpu_type"],
        set_={
            "vram_gb": stmt.excluded.vram_gb,
            "price_per_hour_usd": stmt.excluded.price_per_hour_usd,
        },
    )
    await db.execute(stmt)
    return len(values)


async def sync_live_pricing(db: AsyncSession) -> GpuPricingSyncResponse:
    vendor_results: dict[str, GpuPricingSyncVendorResult] = {}
    total_rows_upserted = 0

    for vendor_key, (get_api_key, fetch_fn) in _PROVIDERS.items():
        api_key = get_api_key()
        if not api_key:
            vendor_results[vendor_key] = GpuPricingSyncVendorResult(
                status="skipped", detail=f"No API key configured for {vendor_key}."
            )
            continue

        try:
            offers = await fetch_fn(api_key)
        except GpuPricingProviderError as exc:
            log.warning("gpu_pricing_sync.provider_failed", vendor=vendor_key, error=str(exc))
            vendor_results[vendor_key] = GpuPricingSyncVendorResult(
                status="failed", detail=str(exc)
            )
            continue

        deduped = _dedupe_cheapest(offers)
        rows_upserted = await _upsert_offers(db, deduped)
        total_rows_upserted += rows_upserted
        vendor_results[vendor_key] = GpuPricingSyncVendorResult(
            status="ok", offers_fetched=len(offers), rows_upserted=rows_upserted
        )

    await db.commit()
    return GpuPricingSyncResponse(vendors=vendor_results, total_rows_upserted=total_rows_upserted)
