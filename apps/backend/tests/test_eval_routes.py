from collections.abc import Iterator
from uuid import uuid4

import psycopg2
import pytest
from core.auth import create_access_token
from core.config import settings
from services import eval_service


def _unique_email() -> str:
    return f"test-eval-{uuid4()}@example.com"


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
def mock_dispatch(monkeypatch) -> list[tuple]:
    calls: list[tuple] = []

    class _FakeDispatch:
        def delay(self, **kwargs) -> None:
            calls.append(kwargs)

    monkeypatch.setattr(eval_service, "dispatch_eval_job", _FakeDispatch())
    return calls


def _register(client, email: str, password: str = "supersecret123") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Eval Tester"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(user: dict) -> dict:
    access_token = create_access_token({"sub": user["id"]})
    return {"Authorization": f"Bearer {access_token}"}


def test_create_compare_job_success(client, emails_to_cleanup, mock_dispatch) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/eval/compare",
        headers=_auth_headers(user),
        json={
            "base_model_id": "gpt2",
            "finetuned_model_id": "gpt2-ft",
            "prompts": ["Hello, world!"],
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user_id"] == user["id"]
    assert data["status"] == "pending"
    assert data["eval_type"] == "compare"
    assert data["base_model_id"] == "gpt2"
    assert data["finetuned_model_id"] == "gpt2-ft"
    assert data["prompts"] == ["Hello, world!"]
    assert len(mock_dispatch) == 1
    assert mock_dispatch[0]["eval_id"] == data["id"]
    assert mock_dispatch[0]["eval_type"] == "compare"


def test_create_compare_job_rejects_empty_prompts(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/eval/compare",
        headers=_auth_headers(user),
        json={"base_model_id": "gpt2", "finetuned_model_id": "gpt2-ft", "prompts": []},
    )

    assert response.status_code == 422


def test_create_compare_job_rejects_unsupported_benchmark(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/eval/compare",
        headers=_auth_headers(user),
        json={
            "base_model_id": "gpt2",
            "finetuned_model_id": "gpt2-ft",
            "prompts": ["hi"],
            "benchmarks": ["not-a-real-benchmark"],
        },
    )

    assert response.status_code == 422


def test_create_benchmark_job_success(client, emails_to_cleanup, mock_dispatch) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/eval/benchmark",
        headers=_auth_headers(user),
        json={"base_model_id": "gpt2", "benchmarks": ["mmlu", "hellaswag"]},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["eval_type"] == "benchmark"
    assert data["benchmarks"] == ["mmlu", "hellaswag"]
    assert data["finetuned_model_id"] is None
    assert len(mock_dispatch) == 1
    assert mock_dispatch[0]["eval_type"] == "benchmark"


def test_list_eval_jobs_scoped_to_user(client, emails_to_cleanup, mock_dispatch) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)

    client.post(
        "/api/v1/eval/benchmark",
        headers=headers,
        json={"base_model_id": "gpt2", "benchmarks": ["mmlu"]},
    )

    response = client.get("/api/v1/eval", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_eval_job_not_found_for_other_user(client, emails_to_cleanup, mock_dispatch) -> None:
    email_a = _unique_email()
    email_b = _unique_email()
    emails_to_cleanup.extend([email_a, email_b])
    user_a = _register(client, email_a)
    user_b = _register(client, email_b)

    create_response = client.post(
        "/api/v1/eval/benchmark",
        headers=_auth_headers(user_a),
        json={"base_model_id": "gpt2", "benchmarks": ["mmlu"]},
    )
    eval_id = create_response.json()["id"]

    response = client.get(f"/api/v1/eval/{eval_id}", headers=_auth_headers(user_b))
    assert response.status_code == 404
