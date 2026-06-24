"""One-shot script to refresh gpu_pricing rows from live RunPod + Lambda Labs
APIs. Run with: uv run python scripts/sync_gpu_pricing.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from core.database import AsyncSessionLocal
from services.gpu_pricing_sync_service import sync_live_pricing

log = structlog.get_logger()


async def run_sync() -> None:
    async with AsyncSessionLocal() as session:
        result = await sync_live_pricing(session)
    log.info(
        "sync_gpu_pricing.completed",
        total_rows_upserted=result.total_rows_upserted,
        cached=result.cached,
        vendors={vendor: payload.model_dump() for vendor, payload in result.vendors.items()},
    )


if __name__ == "__main__":
    asyncio.run(run_sync())
