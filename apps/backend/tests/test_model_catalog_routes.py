from collections.abc import Iterator
from uuid import uuid4

import psycopg2
import pytest
from core.auth import create_access_token
from core.config import settings


def _unique_email() -> str:
    return f"test-catalog-{uuid4()}@example.com"


def _unique_model_id() -> str:
    return f"test-org/test-model-{uuid4()}"


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
def seeded_models() -> Iterator[list[dict]]:
    rows = [
        {
            "model_id": _unique_model_id(),
            "display_name": "Test Model A",
            "family": "test-family",
            "parameter_count_b": 7.0,
            "supports_instruct": True,
        },
        {
            "model_id": _unique_model_id(),
            "display_name": "Test Model B",
            "family": "test-family",
            "parameter_count_b": 13.0,
            "supports_instruct": False,
        },
    ]
    conn = psycopg2.connect(settings.DATABASE_URL_SYNC)
    try:
        with conn, conn.cursor() as cur:
            for row in rows:
                cur.execute(
                    """
                    INSERT INTO model_catalog
                        (model_id, display_name, family, parameter_count_b, supports_instruct)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        row["model_id"],
                        row["display_name"],
                        row["family"],
                        row["parameter_count_b"],
                        row["supports_instruct"],
                    ),
                )
    finally:
        conn.close()

    yield rows

    conn = psycopg2.connect(settings.DATABASE_URL_SYNC)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM model_catalog WHERE model_id = ANY(%s)",
                ([row["model_id"] for row in rows],),
            )
    finally:
        conn.close()


def _register(client, email: str, password: str = "supersecret123") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Catalog Tester"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(user: dict) -> dict:
    access_token = create_access_token({"sub": user["id"]})
    return {"Authorization": f"Bearer {access_token}"}


def test_list_catalog_returns_seeded_models(client, emails_to_cleanup, seeded_models):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.get("/api/v1/models/catalog", headers=_auth_headers(user))

    assert response.status_code == 200, response.text
    returned_ids = {model["model_id"] for model in response.json()}
    for row in seeded_models:
        assert row["model_id"] in returned_ids


def test_get_catalog_model_by_id(client, emails_to_cleanup, seeded_models):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    target = seeded_models[0]

    response = client.get(
        f"/api/v1/models/catalog/{target['model_id']}", headers=_auth_headers(user)
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["model_id"] == target["model_id"]
    assert body["display_name"] == target["display_name"]
    assert body["parameter_count_b"] == target["parameter_count_b"]
    assert body["supports_instruct"] == target["supports_instruct"]


def test_get_catalog_model_not_found(client, emails_to_cleanup):
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.get(
        "/api/v1/models/catalog/no-such-org/no-such-model", headers=_auth_headers(user)
    )

    assert response.status_code == 404, response.text


def test_list_catalog_requires_auth(client):
    response = client.get("/api/v1/models/catalog")
    assert response.status_code == 401


def test_get_catalog_model_requires_auth(client):
    response = client.get("/api/v1/models/catalog/meta-llama/Meta-Llama-3-8B")
    assert response.status_code == 401
