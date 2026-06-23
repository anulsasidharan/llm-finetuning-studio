from collections.abc import Iterator
from uuid import uuid4

import psycopg2
import pytest
from core.auth import create_access_token
from core.config import settings


def _unique_email() -> str:
    return f"test-experiment-{uuid4()}@example.com"


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


def _register(client, email: str, password: str = "supersecret123") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Experiment Tester"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(user: dict) -> dict:
    access_token = create_access_token({"sub": user["id"]})
    return {"Authorization": f"Bearer {access_token}"}


def _create_job(client, headers: dict, **overrides) -> dict:
    payload = {
        "base_model_id": "meta-llama/Meta-Llama-3-8B",
        "methodology": "sft",
        "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
    }
    payload.update(overrides)
    response = client.post("/api/v1/jobs", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_experiment(client, headers: dict, **overrides) -> dict:
    payload = {"name": "Baseline sweep", "description": "Comparing SFT configs"}
    payload.update(overrides)
    response = client.post("/api/v1/experiments", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_experiment_success(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/experiments",
        headers=_auth_headers(user),
        json={"name": "Baseline sweep", "description": "Comparing SFT configs"},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user_id"] == user["id"]
    assert data["name"] == "Baseline sweep"
    assert data["description"] == "Comparing SFT configs"


def test_create_experiment_unauthenticated_returns_401(client) -> None:
    response = client.post("/api/v1/experiments", json={"name": "Baseline sweep"})

    assert response.status_code == 401


def test_list_experiments_returns_only_current_users_experiments(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    _create_experiment(client, headers)

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)
    _create_experiment(client, _auth_headers(other_user))

    response = client.get("/api/v1/experiments", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == user["id"]


def test_get_experiment_returns_experiment(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    created = _create_experiment(client, headers)

    response = client.get(f"/api/v1/experiments/{created['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_experiment_not_found_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.get(f"/api/v1/experiments/{uuid4()}", headers=_auth_headers(user))

    assert response.status_code == 404


def test_get_experiment_scoped_to_owner_returns_404_for_other_users_experiment(
    client, emails_to_cleanup
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    owner = _register(client, email)
    created = _create_experiment(client, _auth_headers(owner))

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)

    response = client.get(f"/api/v1/experiments/{created['id']}", headers=_auth_headers(other_user))

    assert response.status_code == 404


def test_create_run_snapshots_job_metrics(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    experiment = _create_experiment(client, headers)
    job = _create_job(client, headers)

    response = client.post(
        f"/api/v1/experiments/{experiment['id']}/runs",
        headers=headers,
        json={"fine_tune_job_id": job["id"]},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["experiment_id"] == experiment["id"]
    assert data["fine_tune_job_id"] == job["id"]
    assert data["metrics"] == {
        "train_loss": None,
        "eval_loss": None,
        "gpu_utilization_pct": None,
        "vram_used_gb": None,
        "tokens_per_second": None,
    }


def test_create_run_nonexistent_experiment_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    job = _create_job(client, headers)

    response = client.post(
        f"/api/v1/experiments/{uuid4()}/runs",
        headers=headers,
        json={"fine_tune_job_id": job["id"]},
    )

    assert response.status_code == 404


def test_create_run_nonexistent_job_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    experiment = _create_experiment(client, headers)

    response = client.post(
        f"/api/v1/experiments/{experiment['id']}/runs",
        headers=headers,
        json={"fine_tune_job_id": str(uuid4())},
    )

    assert response.status_code == 404


def test_create_run_other_users_job_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    owner = _register(client, email)
    experiment = _create_experiment(client, _auth_headers(owner))

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)
    other_job = _create_job(client, _auth_headers(other_user))

    response = client.post(
        f"/api/v1/experiments/{experiment['id']}/runs",
        headers=_auth_headers(owner),
        json={"fine_tune_job_id": other_job["id"]},
    )

    assert response.status_code == 404


def test_create_run_unauthenticated_returns_401(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    experiment = _create_experiment(client, _auth_headers(user))

    response = client.post(
        f"/api/v1/experiments/{experiment['id']}/runs",
        json={"fine_tune_job_id": str(uuid4())},
    )

    assert response.status_code == 401


def test_compare_experiment_returns_runs_and_metrics_by_name(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    experiment = _create_experiment(client, headers)
    job_a = _create_job(client, headers, methodology="sft")
    job_b = _create_job(
        client,
        headers,
        methodology="lora",
        training_config={
            "learning_rate": 0.0002,
            "num_epochs": 3,
            "batch_size": 4,
            "lora_r": 8,
            "lora_alpha": 16,
        },
    )
    client.post(
        f"/api/v1/experiments/{experiment['id']}/runs",
        headers=headers,
        json={"fine_tune_job_id": job_a["id"]},
    )
    client.post(
        f"/api/v1/experiments/{experiment['id']}/runs",
        headers=headers,
        json={"fine_tune_job_id": job_b["id"]},
    )

    response = client.get(f"/api/v1/experiments/{experiment['id']}/compare", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["experiment_id"] == experiment["id"]
    assert len(data["runs"]) == 2
    assert {run["fine_tune_job_id"] for run in data["runs"]} == {job_a["id"], job_b["id"]}
    assert {run["methodology"] for run in data["runs"]} == {"sft", "lora"}
    assert set(data["metrics_by_name"].keys()) == {
        "train_loss",
        "eval_loss",
        "gpu_utilization_pct",
        "vram_used_gb",
        "tokens_per_second",
    }
    assert data["metrics_by_name"]["train_loss"] == []


def test_compare_experiment_not_found_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.get(f"/api/v1/experiments/{uuid4()}/compare", headers=_auth_headers(user))

    assert response.status_code == 404


def test_compare_experiment_unauthenticated_returns_401(client) -> None:
    response = client.get(f"/api/v1/experiments/{uuid4()}/compare")

    assert response.status_code == 401
