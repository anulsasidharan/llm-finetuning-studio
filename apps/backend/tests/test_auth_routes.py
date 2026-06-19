from collections.abc import Iterator
from uuid import uuid4

import psycopg2
import pytest
from core.auth import create_access_token, create_refresh_token
from core.config import settings


def _unique_email() -> str:
    return f"test-auth-{uuid4()}@example.com"


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


def _register(
    client, email: str, password: str = "supersecret123", full_name: str = "Test User"
) -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_register_creates_user(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)

    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "supersecret123", "full_name": "New User"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == email
    assert data["full_name"] == "New User"
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data


def test_register_duplicate_email_returns_409(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    _register(client, email)

    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "anotherpass123", "full_name": "Dup User"},
    )

    assert response.status_code == 409


def test_login_success_returns_tokens(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    _register(client, email, password="correctpass123")

    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "correctpass123"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]


def test_login_wrong_password_returns_401(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    _register(client, email, password="correctpass123")

    response = client.post("/api/v1/auth/login", json={"email": email, "password": "wrongpass123"})

    assert response.status_code == 401


def test_refresh_success_returns_new_access_token(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    refresh_token = create_refresh_token({"sub": user["id"]})

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})

    assert response.status_code == 200
    data = response.json()
    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_refresh_invalid_token_returns_401(client) -> None:
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})

    assert response.status_code == 401


def test_me_returns_current_user(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    access_token = create_access_token({"sub": user["id"]})

    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"})

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == email


def test_me_unauthenticated_returns_401(client) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_logout_returns_204(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    access_token = create_access_token({"sub": user["id"]})

    response = client.post(
        "/api/v1/auth/logout", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 204


def test_logout_unauthenticated_returns_401(client) -> None:
    response = client.post("/api/v1/auth/logout")

    assert response.status_code == 401
