import subprocess
import sys
from pathlib import Path

import psycopg2
from core.config import settings
from scripts.seed_data import GPU_PRICING_SEED, MODEL_CATALOG_SEED

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def test_model_catalog_seed_has_unique_model_ids() -> None:
    model_ids = [row["model_id"] for row in MODEL_CATALOG_SEED]
    assert len(model_ids) == len(set(model_ids))
    assert len(model_ids) == 13


def test_gpu_pricing_seed_covers_all_vendors() -> None:
    vendors = {row["vendor"] for row in GPU_PRICING_SEED}
    assert vendors == {"AWS", "GCP", "Azure", "RunPod", "Lambda Labs"}


def _run_seed_script() -> None:
    # Runs the script as a real subprocess (its own fresh asyncio engine)
    # rather than importing+awaiting it in-process: the pytest process
    # already has a long-lived async DB engine bound to conftest's
    # session-scoped event loop, and mixing in a second ad-hoc loop here
    # crashes with cross-loop asyncpg errors (the same class of bug fixed
    # for tests/conftest.py's client fixture in PHASE1-WEEK2-012).
    result = subprocess.run(
        [sys.executable, "scripts/seed_data.py"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_seed_script_seeds_database_idempotently() -> None:
    _run_seed_script()
    _run_seed_script()

    conn = psycopg2.connect(settings.DATABASE_URL_SYNC)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM model_catalog")
            assert cur.fetchone()[0] == len(MODEL_CATALOG_SEED)

            cur.execute(
                "SELECT display_name, family, supports_instruct FROM model_catalog "
                "WHERE model_id = %s",
                ("meta-llama/Meta-Llama-3-8B",),
            )
            display_name, family, supports_instruct = cur.fetchone()
            assert display_name == "Llama 3 8B"
            assert family == "Llama-3"
            assert supports_instruct is False

            cur.execute("SELECT count(*) FROM gpu_pricing")
            assert cur.fetchone()[0] == len(GPU_PRICING_SEED)

            cur.execute(
                "SELECT vram_gb, price_per_hour_usd FROM gpu_pricing "
                "WHERE vendor = %s AND gpu_type = %s",
                ("AWS", "A100-80GB"),
            )
            vram_gb, price_per_hour_usd = cur.fetchone()
            assert vram_gb == 80
            assert float(price_per_hour_usd) == 4.10
    finally:
        conn.close()
