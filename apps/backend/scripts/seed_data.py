"""One-shot, idempotent seed script for the model catalog and GPU pricing
reference tables. Run with: uv run python scripts/seed_data.py
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import structlog
from core.database import AsyncSessionLocal
from models import GpuPricing, ModelCatalog
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

log = structlog.get_logger()

MODEL_CATALOG_SEED: list[dict[str, str | float | bool]] = [
    {
        "model_id": "meta-llama/Meta-Llama-3-8B",
        "display_name": "Llama 3 8B",
        "family": "Llama-3",
        "parameter_count_b": 8.0,
        "supports_instruct": False,
    },
    {
        "model_id": "meta-llama/Meta-Llama-3-8B-Instruct",
        "display_name": "Llama 3 8B Instruct",
        "family": "Llama-3",
        "parameter_count_b": 8.0,
        "supports_instruct": True,
    },
    {
        "model_id": "meta-llama/Meta-Llama-3-70B",
        "display_name": "Llama 3 70B",
        "family": "Llama-3",
        "parameter_count_b": 70.0,
        "supports_instruct": False,
    },
    {
        "model_id": "mistralai/Mistral-7B-v0.3",
        "display_name": "Mistral 7B v0.3",
        "family": "Mistral",
        "parameter_count_b": 7.0,
        "supports_instruct": False,
    },
    {
        "model_id": "mistralai/Mistral-7B-Instruct-v0.3",
        "display_name": "Mistral 7B Instruct v0.3",
        "family": "Mistral",
        "parameter_count_b": 7.0,
        "supports_instruct": True,
    },
    {
        "model_id": "microsoft/Phi-3-mini-4k-instruct",
        "display_name": "Phi-3 Mini 4K Instruct",
        "family": "Phi-3",
        "parameter_count_b": 3.8,
        "supports_instruct": True,
    },
    {
        "model_id": "microsoft/Phi-3-medium-4k-instruct",
        "display_name": "Phi-3 Medium 4K Instruct",
        "family": "Phi-3",
        "parameter_count_b": 14.0,
        "supports_instruct": True,
    },
    {
        "model_id": "Qwen/Qwen2-7B",
        "display_name": "Qwen2 7B",
        "family": "Qwen2",
        "parameter_count_b": 7.0,
        "supports_instruct": False,
    },
    {
        "model_id": "Qwen/Qwen2-72B",
        "display_name": "Qwen2 72B",
        "family": "Qwen2",
        "parameter_count_b": 72.0,
        "supports_instruct": False,
    },
    {
        "model_id": "google/gemma-2-9b",
        "display_name": "Gemma 2 9B",
        "family": "Gemma-2",
        "parameter_count_b": 9.0,
        "supports_instruct": False,
    },
    {
        "model_id": "google/gemma-2-27b",
        "display_name": "Gemma 2 27B",
        "family": "Gemma-2",
        "parameter_count_b": 27.0,
        "supports_instruct": False,
    },
    {
        "model_id": "codellama/CodeLlama-7b-hf",
        "display_name": "CodeLlama 7B",
        "family": "CodeLlama",
        "parameter_count_b": 7.0,
        "supports_instruct": False,
    },
    {
        "model_id": "codellama/CodeLlama-34b-hf",
        "display_name": "CodeLlama 34B",
        "family": "CodeLlama",
        "parameter_count_b": 34.0,
        "supports_instruct": False,
    },
]

GPU_PRICING_SEED: list[dict[str, str | int | float]] = [
    {"vendor": "AWS", "gpu_type": "A100-80GB", "vram_gb": 80, "price_per_hour_usd": 4.10},
    {"vendor": "AWS", "gpu_type": "V100-16GB", "vram_gb": 16, "price_per_hour_usd": 3.06},
    {"vendor": "GCP", "gpu_type": "A100-80GB", "vram_gb": 80, "price_per_hour_usd": 3.93},
    {"vendor": "GCP", "gpu_type": "T4-16GB", "vram_gb": 16, "price_per_hour_usd": 0.35},
    {"vendor": "Azure", "gpu_type": "A100-80GB", "vram_gb": 80, "price_per_hour_usd": 3.40},
    {"vendor": "Azure", "gpu_type": "V100-16GB", "vram_gb": 16, "price_per_hour_usd": 3.06},
    {"vendor": "RunPod", "gpu_type": "A100-80GB", "vram_gb": 80, "price_per_hour_usd": 1.89},
    {"vendor": "RunPod", "gpu_type": "RTX4090-24GB", "vram_gb": 24, "price_per_hour_usd": 0.44},
    {"vendor": "Lambda Labs", "gpu_type": "A100-80GB", "vram_gb": 80, "price_per_hour_usd": 1.29},
    {"vendor": "Lambda Labs", "gpu_type": "H100-80GB", "vram_gb": 80, "price_per_hour_usd": 2.49},
]


async def seed_model_catalog(session: AsyncSession) -> int:
    stmt = insert(ModelCatalog).values(MODEL_CATALOG_SEED)
    stmt = stmt.on_conflict_do_update(
        index_elements=["model_id"],
        set_={
            "display_name": stmt.excluded.display_name,
            "family": stmt.excluded.family,
            "parameter_count_b": stmt.excluded.parameter_count_b,
            "supports_instruct": stmt.excluded.supports_instruct,
        },
    )
    await session.execute(stmt)
    return len(MODEL_CATALOG_SEED)


async def seed_gpu_pricing(session: AsyncSession) -> int:
    stmt = insert(GpuPricing).values(GPU_PRICING_SEED)
    stmt = stmt.on_conflict_do_update(
        index_elements=["vendor", "gpu_type"],
        set_={
            "vram_gb": stmt.excluded.vram_gb,
            "price_per_hour_usd": stmt.excluded.price_per_hour_usd,
        },
    )
    await session.execute(stmt)
    return len(GPU_PRICING_SEED)


async def run_seed() -> None:
    async with AsyncSessionLocal() as session:
        model_count = await seed_model_catalog(session)
        gpu_count = await seed_gpu_pricing(session)
        await session.commit()
    log.info(
        "seed_data.completed",
        model_catalog_rows=model_count,
        gpu_pricing_rows=gpu_count,
    )


if __name__ == "__main__":
    asyncio.run(run_seed())
