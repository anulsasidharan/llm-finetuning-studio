from collections.abc import Iterator
from uuid import uuid4

import psycopg2
import pytest
from core.auth import create_access_token
from core.config import settings
from services import dataset_service, job_service


def _unique_email() -> str:
    return f"test-job-{uuid4()}@example.com"


def _valid_lora_config() -> dict:
    return {
        "learning_rate": 0.0002,
        "num_epochs": 3,
        "batch_size": 4,
        "lora_r": 8,
        "lora_alpha": 16,
    }


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
def mock_minio_upload(monkeypatch) -> list[tuple]:
    calls: list[tuple] = []

    def _fake_upload_file(bucket, object_name, data, length, content_type) -> None:
        calls.append((bucket, object_name, length, content_type))

    monkeypatch.setattr(dataset_service, "upload_file", _fake_upload_file)
    return calls


@pytest.fixture
def mock_dispatch(monkeypatch) -> list[tuple]:
    calls: list[tuple] = []

    class _FakeDispatch:
        def delay(self, **kwargs) -> None:
            calls.append(kwargs)

    monkeypatch.setattr(job_service, "dispatch_training_job", _FakeDispatch())
    return calls


def _register(client, email: str, password: str = "supersecret123") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Job Tester"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(user: dict) -> dict:
    access_token = create_access_token({"sub": user["id"]})
    return {"Authorization": f"Bearer {access_token}"}


def _upload_dataset(client, headers: dict) -> dict:
    response = client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={"file": ("sample.jsonl", b'{"instruction": "a", "output": "b"}\n', "text/plain")},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_job_success(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/jobs",
        headers=_auth_headers(user),
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "lora",
            "training_config": _valid_lora_config(),
        },
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user_id"] == user["id"]
    assert data["status"] == "pending"
    assert data["methodology"] == "lora"
    assert data["dataset_id"] is None


def test_create_job_with_dataset_id(client, emails_to_cleanup, mock_minio_upload) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    dataset = _upload_dataset(client, headers)

    response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
            "dataset_id": dataset["id"],
        },
    )

    assert response.status_code == 201, response.text
    assert response.json()["dataset_id"] == dataset["id"]


def test_create_job_dispatches_training_task_without_dataset(
    client, emails_to_cleanup, mock_dispatch
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/jobs",
        headers=_auth_headers(user),
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
        },
    )

    job_id = response.json()["id"]
    assert len(mock_dispatch) == 1
    assert mock_dispatch[0]["job_id"] == job_id
    assert mock_dispatch[0]["dataset_storage_path"] is None
    assert mock_dispatch[0]["dataset_format"] is None


def test_create_job_dispatches_training_task_with_dataset(
    client, emails_to_cleanup, mock_minio_upload, mock_dispatch
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    dataset = _upload_dataset(client, headers)

    response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
            "dataset_id": dataset["id"],
        },
    )

    job_id = response.json()["id"]
    assert len(mock_dispatch) == 1
    assert mock_dispatch[0]["job_id"] == job_id
    assert mock_dispatch[0]["dataset_storage_path"] == dataset["storage_path"]
    assert mock_dispatch[0]["dataset_format"] == dataset["format"]


def test_create_job_invalid_methodology_rejected(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/jobs",
        headers=_auth_headers(user),
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "not-a-real-method",
            "training_config": _valid_lora_config(),
        },
    )

    assert response.status_code == 422


def test_create_job_missing_common_keys_rejected(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/jobs",
        headers=_auth_headers(user),
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001},
        },
    )

    assert response.status_code == 422


def test_create_job_missing_method_specific_keys_rejected(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/jobs",
        headers=_auth_headers(user),
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "lora",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
        },
    )

    assert response.status_code == 422


def test_create_job_nonexistent_dataset_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/jobs",
        headers=_auth_headers(user),
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
            "dataset_id": str(uuid4()),
        },
    )

    assert response.status_code == 404


def test_create_job_other_users_dataset_returns_404(
    client, emails_to_cleanup, mock_minio_upload
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    owner = _register(client, email)
    dataset = _upload_dataset(client, _auth_headers(owner))

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)

    response = client.post(
        "/api/v1/jobs",
        headers=_auth_headers(other_user),
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
            "dataset_id": dataset["id"],
        },
    )

    assert response.status_code == 404


def test_create_job_unauthenticated_returns_401(client) -> None:
    response = client.post(
        "/api/v1/jobs",
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
        },
    )

    assert response.status_code == 401


def test_list_jobs_returns_only_current_users_jobs(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)

    client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
        },
    )

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)
    client.post(
        "/api/v1/jobs",
        headers=_auth_headers(other_user),
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
        },
    )

    response = client.get("/api/v1/jobs", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == user["id"]


def test_get_job_returns_job(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)

    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
        },
    ).json()

    response = client.get(f"/api/v1/jobs/{created['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_job_not_found_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.get(f"/api/v1/jobs/{uuid4()}", headers=_auth_headers(user))

    assert response.status_code == 404


def test_get_job_scoped_to_owner_returns_404_for_other_users_job(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    owner = _register(client, email)
    created = client.post(
        "/api/v1/jobs",
        headers=_auth_headers(owner),
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
        },
    ).json()

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)

    response = client.get(f"/api/v1/jobs/{created['id']}", headers=_auth_headers(other_user))

    assert response.status_code == 404


def test_get_job_unauthenticated_returns_401(client) -> None:
    response = client.get(f"/api/v1/jobs/{uuid4()}")

    assert response.status_code == 401


def test_get_job_config_returns_training_config(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    config = {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2}

    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": config,
        },
    ).json()

    response = client.get(f"/api/v1/jobs/{created['id']}/config", headers=headers)

    assert response.status_code == 200
    assert response.json()["training_config"] == config


def test_get_job_config_not_found_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.get(f"/api/v1/jobs/{uuid4()}/config", headers=_auth_headers(user))

    assert response.status_code == 404


def test_get_job_config_unauthenticated_returns_401(client) -> None:
    response = client.get(f"/api/v1/jobs/{uuid4()}/config")

    assert response.status_code == 401


@pytest.fixture
def mock_launch_job(monkeypatch):
    from services.cloud_launchers.base import LaunchedPod

    async def _fake_launch_job(job):
        return LaunchedPod(
            pod_id="pod-abc123", image_name="orionvexa/fts-training-engine", machine_id="machine-1"
        )

    monkeypatch.setattr(job_service.cloud_launch_service, "launch_job", _fake_launch_job)


def test_launch_cloud_job_success(
    client, emails_to_cleanup, mock_dispatch, mock_launch_job
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)

    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
            "gpu_type": "A10080GBPCIe",
            "cloud_vendor": "RunPod",
        },
    ).json()

    response = client.post(f"/api/v1/jobs/{created['id']}/launch-cloud", headers=headers)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["pod_id"] == "pod-abc123"
    assert data["image_name"] == "orionvexa/fts-training-engine"
    assert data["machine_id"] == "machine-1"


def test_launch_cloud_job_unsupported_vendor_returns_422(
    client, emails_to_cleanup, mock_dispatch
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)

    created = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
        },
    ).json()

    response = client.post(f"/api/v1/jobs/{created['id']}/launch-cloud", headers=headers)

    assert response.status_code == 422


def test_launch_cloud_job_not_found_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(f"/api/v1/jobs/{uuid4()}/launch-cloud", headers=_auth_headers(user))

    assert response.status_code == 404


def test_launch_cloud_job_scoped_to_owner_returns_404_for_other_users_job(
    client, emails_to_cleanup, mock_dispatch
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    owner = _register(client, email)
    created = client.post(
        "/api/v1/jobs",
        headers=_auth_headers(owner),
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
            "gpu_type": "A10080GBPCIe",
            "cloud_vendor": "RunPod",
        },
    ).json()

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)

    response = client.post(
        f"/api/v1/jobs/{created['id']}/launch-cloud", headers=_auth_headers(other_user)
    )

    assert response.status_code == 404


def test_launch_cloud_job_unauthenticated_returns_401(client) -> None:
    response = client.post(f"/api/v1/jobs/{uuid4()}/launch-cloud")

    assert response.status_code == 401
