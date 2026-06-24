from collections.abc import Iterator
from uuid import uuid4

import psycopg2
import pytest
from core.auth import create_access_token
from core.config import settings
from services.gpu_pricing_providers.base import GpuPricingProviderError, NormalizedGpuOffer


def _unique_email() -> str:
    return f"test-gpu-sync-{uuid4()}@example.com"


@pytest.fixture
def emails_to_cleanup() -> Iterator[list[str]]:
    emails: list[str] = []
    yield emails
    if emails:
        conn = psycopg2.connect(settings.DATABASE_URL_SYNC)
        try:
            with conn, conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE email = ANY(%s)", (emails,))
        finally:
            conn.close()


@pytest.fixture
def gpu_pricing_rows_to_cleanup() -> Iterator[list[str]]:
    gpu_types: list[str] = []
    yield gpu_types
    if gpu_types:
        conn = psycopg2.connect(settings.DATABASE_URL_SYNC)
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM gpu_pricing WHERE gpu_type = ANY(%s)",
                    (gpu_types,),
                )
        finally:
            conn.close()


def _register(client, email: str, password: str = "supersecret123") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "GPU Sync Tester"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(user: dict) -> dict:
    access_token = create_access_token({"sub": user["id"]})
    return {"Authorization": f"Bearer {access_token}"}


def test_sync_pricing_requires_auth(client):
    response = client.post("/api/v1/gpu/sync-pricing")
    assert response.status_code == 401


def test_sync_pricing_skips_vendor_without_api_key(client, monkeypatch, emails_to_cleanup):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    monkeypatch.setattr(settings, "RUNPOD_API_KEY", "")
    monkeypatch.setattr(settings, "LAMBDA_LABS_API_KEY", "")

    response = client.post("/api/v1/gpu/sync-pricing", headers=_auth_headers(user))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_rows_upserted"] == 0
    assert body["vendors"]["runpod"]["status"] == "skipped"
    assert body["vendors"]["lambda_labs"]["status"] == "skipped"


def test_sync_pricing_upserts_offers_and_reports_failure(
    client, monkeypatch, emails_to_cleanup, gpu_pricing_rows_to_cleanup
):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    gpu_type = f"Test-Sync-A100-{uuid4()}"
    gpu_pricing_rows_to_cleanup.append(gpu_type)

    monkeypatch.setattr(settings, "RUNPOD_API_KEY", "fake-runpod-key")
    monkeypatch.setattr(settings, "LAMBDA_LABS_API_KEY", "fake-lambda-key")

    async def fake_runpod(api_key: str, client=None) -> list[NormalizedGpuOffer]:
        assert api_key == "fake-runpod-key"
        return [
            NormalizedGpuOffer(
                vendor="RunPod", gpu_type=gpu_type, vram_gb=80, price_per_hour_usd=1.5
            )
        ]

    async def fake_lambda_labs(api_key: str, client=None) -> list[NormalizedGpuOffer]:
        assert api_key == "fake-lambda-key"
        raise GpuPricingProviderError("simulated outage")

    monkeypatch.setattr(
        "services.gpu_pricing_providers.runpod_provider.fetch_runpod_pricing", fake_runpod
    )
    monkeypatch.setattr(
        "services.gpu_pricing_providers.lambda_labs_provider.fetch_lambda_labs_pricing",
        fake_lambda_labs,
    )

    response = client.post("/api/v1/gpu/sync-pricing", headers=_auth_headers(user))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["total_rows_upserted"] == 1
    assert body["vendors"]["runpod"] == {
        "status": "ok",
        "offers_fetched": 1,
        "rows_upserted": 1,
        "detail": None,
    }
    assert body["vendors"]["lambda_labs"]["status"] == "failed"
    assert "simulated outage" in body["vendors"]["lambda_labs"]["detail"]

    conn = psycopg2.connect(settings.DATABASE_URL_SYNC)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT vendor, price_per_hour_usd FROM gpu_pricing WHERE gpu_type = %s",
                (gpu_type,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    assert row is not None
    assert row[0] == "RunPod"
    assert float(row[1]) == 1.5


def test_sync_pricing_dedupes_same_gpu_type_keeping_cheapest(
    client, monkeypatch, emails_to_cleanup, gpu_pricing_rows_to_cleanup
):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    gpu_type = f"Test-Sync-Dupe-{uuid4()}"
    gpu_pricing_rows_to_cleanup.append(gpu_type)

    monkeypatch.setattr(settings, "RUNPOD_API_KEY", "fake-runpod-key")
    monkeypatch.setattr(settings, "LAMBDA_LABS_API_KEY", "")

    async def fake_runpod(api_key: str, client=None) -> list[NormalizedGpuOffer]:
        return [
            NormalizedGpuOffer(
                vendor="RunPod", gpu_type=gpu_type, vram_gb=80, price_per_hour_usd=2.0
            ),
            NormalizedGpuOffer(
                vendor="RunPod", gpu_type=gpu_type, vram_gb=80, price_per_hour_usd=1.2
            ),
        ]

    monkeypatch.setattr(
        "services.gpu_pricing_providers.runpod_provider.fetch_runpod_pricing", fake_runpod
    )

    response = client.post("/api/v1/gpu/sync-pricing", headers=_auth_headers(user))

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["vendors"]["runpod"]["offers_fetched"] == 2
    assert body["vendors"]["runpod"]["rows_upserted"] == 1

    conn = psycopg2.connect(settings.DATABASE_URL_SYNC)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "SELECT price_per_hour_usd FROM gpu_pricing WHERE gpu_type = %s",
                (gpu_type,),
            )
            row = cur.fetchone()
    finally:
        conn.close()
    assert float(row[0]) == 1.2
