from collections.abc import Iterator
from uuid import uuid4

import psycopg2
import pytest
from core.auth import create_access_token
from core.config import settings


def _unique_email() -> str:
    return f"test-gpu-{uuid4()}@example.com"


def _unique_gpu_type(label: str) -> str:
    return f"Test-{label}-{uuid4()}"


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
def seeded_gpu_pricing() -> Iterator[list[dict]]:
    vendor = f"TestVendor-{uuid4()}"
    rows = [
        {
            "vendor": vendor,
            "gpu_type": _unique_gpu_type("A100"),
            "vram_gb": 80,
            "price_per_hour_usd": 2.5,
        },
        {
            "vendor": vendor,
            "gpu_type": _unique_gpu_type("T4"),
            "vram_gb": 16,
            "price_per_hour_usd": 0.5,
        },
    ]
    conn = psycopg2.connect(settings.DATABASE_URL_SYNC)
    try:
        with conn, conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    """
                    INSERT INTO gpu_pricing (vendor, gpu_type, vram_gb, price_per_hour_usd)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (row["vendor"], row["gpu_type"], row["vram_gb"], row["price_per_hour_usd"]),
                )
    finally:
        conn.close()

    yield rows

    conn = psycopg2.connect(settings.DATABASE_URL_SYNC)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM gpu_pricing WHERE gpu_type = ANY(%s)",
                ([row["gpu_type"] for row in rows],),
            )
    finally:
        conn.close()


def _register(client, email: str, password: str = "supersecret123") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "GPU Tester"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(user: dict) -> dict:
    access_token = create_access_token({"sub": user["id"]})
    return {"Authorization": f"Bearer {access_token}"}


def test_list_instances_returns_seeded_rows(client, emails_to_cleanup, seeded_gpu_pricing):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.get("/api/v1/gpu/instances", headers=_auth_headers(user))

    assert response.status_code == 200, response.text
    returned_types = {row["gpu_type"] for row in response.json()}
    for row in seeded_gpu_pricing:
        assert row["gpu_type"] in returned_types


def test_list_instances_filters_by_vendor(client, emails_to_cleanup, seeded_gpu_pricing):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    vendor = seeded_gpu_pricing[0]["vendor"]

    response = client.get(
        "/api/v1/gpu/instances", params={"vendor": vendor}, headers=_auth_headers(user)
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert len(body) == len(seeded_gpu_pricing)
    assert all(row["vendor"] == vendor for row in body)


def test_get_pricing_returns_matching_row(client, emails_to_cleanup, seeded_gpu_pricing):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    target = seeded_gpu_pricing[0]

    response = client.get(
        "/api/v1/gpu/pricing",
        params={"vendor": target["vendor"], "gpu_type": target["gpu_type"]},
        headers=_auth_headers(user),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["vendor"] == target["vendor"]
    assert body["gpu_type"] == target["gpu_type"]
    assert float(body["price_per_hour_usd"]) == target["price_per_hour_usd"]


def test_get_pricing_not_found(client, emails_to_cleanup):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.get(
        "/api/v1/gpu/pricing",
        params={"vendor": "NoSuchVendor", "gpu_type": "NoSuchType"},
        headers=_auth_headers(user),
    )

    assert response.status_code == 404, response.text


def test_list_instances_requires_auth(client):
    response = client.get("/api/v1/gpu/instances")
    assert response.status_code == 401


def test_get_pricing_requires_auth(client):
    response = client.get("/api/v1/gpu/pricing", params={"vendor": "AWS", "gpu_type": "A100-80GB"})
    assert response.status_code == 401


def test_estimate_cost_with_hours(client, emails_to_cleanup, seeded_gpu_pricing):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    target = seeded_gpu_pricing[0]

    response = client.post(
        "/api/v1/gpu/estimate",
        json={"vendor": target["vendor"], "gpu_type": target["gpu_type"], "hours": 10},
        headers=_auth_headers(user),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["estimated_hours"] == 10
    assert body["estimated_cost_usd"] == target["price_per_hour_usd"] * 10


def test_estimate_cost_with_training_params(client, emails_to_cleanup, seeded_gpu_pricing):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    target = seeded_gpu_pricing[0]

    response = client.post(
        "/api/v1/gpu/estimate",
        json={
            "vendor": target["vendor"],
            "gpu_type": target["gpu_type"],
            "methodology": "lora",
            "num_epochs": 3,
            "dataset_row_count": 1000,
            "batch_size": 4,
            "gradient_accumulation_steps": 1,
        },
        headers=_auth_headers(user),
    )

    assert response.status_code == 200, response.text
    body = response.json()
    # total_steps = ceil(1000 * 3 / 4) = 750, seconds_per_step (lora) = 1.8s -> 0.375 hours
    assert body["estimated_hours"] == 0.375
    assert body["estimated_cost_usd"] == round(0.375 * target["price_per_hour_usd"], 2)


def test_estimate_cost_missing_params_returns_422(client, emails_to_cleanup, seeded_gpu_pricing):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    target = seeded_gpu_pricing[0]

    response = client.post(
        "/api/v1/gpu/estimate",
        json={"vendor": target["vendor"], "gpu_type": target["gpu_type"], "num_epochs": 3},
        headers=_auth_headers(user),
    )

    assert response.status_code == 422, response.text


def test_estimate_cost_not_found(client, emails_to_cleanup):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/gpu/estimate",
        json={"vendor": "NoSuchVendor", "gpu_type": "NoSuchType", "hours": 5},
        headers=_auth_headers(user),
    )

    assert response.status_code == 404, response.text


def test_estimate_cost_requires_auth(client):
    response = client.post(
        "/api/v1/gpu/estimate",
        json={"vendor": "AWS", "gpu_type": "A100-80GB", "hours": 5},
    )
    assert response.status_code == 401


def test_forecast_cost_returns_all_matching_options_sorted_cheapest_first(
    client, emails_to_cleanup, seeded_gpu_pricing
):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    vendor = seeded_gpu_pricing[0]["vendor"]

    response = client.post(
        "/api/v1/gpu/forecast",
        json={"vendor": vendor, "hours": 10},
        headers=_auth_headers(user),
    )

    assert response.status_code == 200, response.text
    options = response.json()["options"]
    assert len(options) == len(seeded_gpu_pricing)
    assert [o["estimated_cost_usd"] for o in options] == sorted(
        o["estimated_cost_usd"] for o in options
    )
    cheapest = min(seeded_gpu_pricing, key=lambda row: row["price_per_hour_usd"])
    assert options[0]["gpu_type"] == cheapest["gpu_type"]
    assert options[0]["estimated_cost_usd"] == cheapest["price_per_hour_usd"] * 10


def test_forecast_cost_filters_by_min_vram_gb(client, emails_to_cleanup, seeded_gpu_pricing):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    vendor = seeded_gpu_pricing[0]["vendor"]

    response = client.post(
        "/api/v1/gpu/forecast",
        json={"vendor": vendor, "min_vram_gb": 80, "hours": 5},
        headers=_auth_headers(user),
    )

    assert response.status_code == 200, response.text
    options = response.json()["options"]
    assert len(options) == 1
    assert all(o["vram_gb"] >= 80 for o in options)


def test_forecast_cost_with_training_params(client, emails_to_cleanup, seeded_gpu_pricing):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    vendor = seeded_gpu_pricing[0]["vendor"]

    response = client.post(
        "/api/v1/gpu/forecast",
        json={
            "vendor": vendor,
            "methodology": "lora",
            "num_epochs": 3,
            "dataset_row_count": 1000,
            "batch_size": 4,
            "gradient_accumulation_steps": 1,
        },
        headers=_auth_headers(user),
    )

    assert response.status_code == 200, response.text
    options = response.json()["options"]
    # total_steps = ceil(1000 * 3 / 4) = 750, seconds_per_step (lora) = 1.8s -> 0.375 hours
    assert all(o["estimated_hours"] == 0.375 for o in options)
    for option in options:
        assert option["estimated_cost_usd"] == round(0.375 * option["price_per_hour_usd"], 2)


def test_forecast_cost_missing_params_returns_422(client, emails_to_cleanup, seeded_gpu_pricing):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    vendor = seeded_gpu_pricing[0]["vendor"]

    response = client.post(
        "/api/v1/gpu/forecast",
        json={"vendor": vendor, "num_epochs": 3},
        headers=_auth_headers(user),
    )

    assert response.status_code == 422, response.text


def test_forecast_cost_no_matching_instances_returns_404(client, emails_to_cleanup):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/gpu/forecast",
        json={"vendor": "NoSuchVendor", "hours": 5},
        headers=_auth_headers(user),
    )

    assert response.status_code == 404, response.text


def test_forecast_cost_requires_auth(client):
    response = client.post("/api/v1/gpu/forecast", json={"hours": 5})
    assert response.status_code == 401
