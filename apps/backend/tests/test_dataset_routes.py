import json
from collections.abc import Iterator
from uuid import uuid4

import psycopg2
import pytest
from core.auth import create_access_token
from core.config import settings
from services import dataset_service

EN_SENTENCE = (
    "This is a sufficiently long English sentence written to make the "
    "language detector confident about its result."
)


def _unique_email() -> str:
    return f"test-dataset-{uuid4()}@example.com"


def _alpaca_jsonl(output: str = EN_SENTENCE) -> bytes:
    row = json.dumps({"instruction": "Summarize.", "input": "", "output": output})
    return (row + "\n").encode()


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
def mock_minio_download(monkeypatch):
    contents_by_object_name: dict[str, bytes] = {}

    def _fake_download_file(bucket, object_name) -> bytes:
        return contents_by_object_name[object_name]

    monkeypatch.setattr(dataset_service, "download_file", _fake_download_file)
    return contents_by_object_name


def _register(client, email: str, password: str = "supersecret123") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Dataset Tester"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _upload_dataset(
    client, headers: dict, mock_minio_download: dict, content: bytes, filename: str = "sample.jsonl"
) -> dict:
    response = client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={"file": (filename, content, "text/plain")},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    mock_minio_download[data["storage_path"]] = content
    return data


def _auth_headers(user: dict) -> dict:
    access_token = create_access_token({"sub": user["id"]})
    return {"Authorization": f"Bearer {access_token}"}


def test_upload_dataset_success(client, emails_to_cleanup, mock_minio_upload) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    content = b'{"instruction": "a", "output": "b"}\n{"instruction": "c", "output": "d"}\n'
    response = client.post(
        "/api/v1/datasets/upload",
        headers=_auth_headers(user),
        files={"file": ("sample.jsonl", content, "text/plain")},
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["user_id"] == user["id"]
    assert data["name"] == "sample.jsonl"
    assert data["format"] == "unknown"
    assert data["row_count"] == 2
    assert data["size_bytes"] == len(content)
    assert len(mock_minio_upload) == 1


def test_upload_dataset_oversized_rejected(client, emails_to_cleanup, monkeypatch) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 0)

    response = client.post(
        "/api/v1/datasets/upload",
        headers=_auth_headers(user),
        files={"file": ("sample.jsonl", b'{"a": 1}\n', "text/plain")},
    )

    assert response.status_code == 422


def test_upload_dataset_wrong_content_type_rejected(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(
        "/api/v1/datasets/upload",
        headers=_auth_headers(user),
        files={"file": ("sample.jsonl", b'{"a": 1}\n', "image/png")},
    )

    assert response.status_code == 422


def test_upload_dataset_unauthenticated_returns_401(client) -> None:
    response = client.post(
        "/api/v1/datasets/upload",
        files={"file": ("sample.jsonl", b'{"a": 1}\n', "text/plain")},
    )

    assert response.status_code == 401


def test_list_datasets_returns_only_current_users_datasets(
    client, emails_to_cleanup, mock_minio_upload
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)

    client.post(
        "/api/v1/datasets/upload",
        headers=headers,
        files={"file": ("sample.jsonl", b'{"a": 1}\n', "text/plain")},
    )

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)
    client.post(
        "/api/v1/datasets/upload",
        headers=_auth_headers(other_user),
        files={"file": ("other.jsonl", b'{"a": 1}\n', "text/plain")},
    )

    response = client.get("/api/v1/datasets", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["user_id"] == user["id"]


def test_get_dataset_returns_dataset(
    client, emails_to_cleanup, mock_minio_upload, mock_minio_download
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    dataset = _upload_dataset(client, headers, mock_minio_download, _alpaca_jsonl())

    response = client.get(f"/api/v1/datasets/{dataset['id']}", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["id"] == dataset["id"]


def test_get_dataset_not_found_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.get(f"/api/v1/datasets/{uuid4()}", headers=_auth_headers(user))

    assert response.status_code == 404


def test_get_dataset_scoped_to_owner_returns_404_for_other_users_dataset(
    client, emails_to_cleanup, mock_minio_upload, mock_minio_download
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    owner = _register(client, email)
    dataset = _upload_dataset(client, _auth_headers(owner), mock_minio_download, _alpaca_jsonl())

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)

    response = client.get(f"/api/v1/datasets/{dataset['id']}", headers=_auth_headers(other_user))

    assert response.status_code == 404


def test_get_dataset_unauthenticated_returns_401(client) -> None:
    response = client.get(f"/api/v1/datasets/{uuid4()}")

    assert response.status_code == 401


def test_format_dataset_detects_alpaca_format(
    client, emails_to_cleanup, mock_minio_upload, mock_minio_download
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    dataset = _upload_dataset(client, headers, mock_minio_download, _alpaca_jsonl())

    response = client.post(f"/api/v1/datasets/{dataset['id']}/format", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["format"] == "alpaca"


def test_format_dataset_unrecognized_row_rejected(
    client, emails_to_cleanup, mock_minio_upload, mock_minio_download
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    dataset = _upload_dataset(client, headers, mock_minio_download, b'{"foo": "bar"}\n')

    response = client.post(f"/api/v1/datasets/{dataset['id']}/format", headers=headers)

    assert response.status_code == 422


def test_format_dataset_not_found_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(f"/api/v1/datasets/{uuid4()}/format", headers=_auth_headers(user))

    assert response.status_code == 404


def test_format_dataset_scoped_to_owner_returns_404_for_other_users_dataset(
    client, emails_to_cleanup, mock_minio_upload, mock_minio_download
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    owner = _register(client, email)
    dataset = _upload_dataset(client, _auth_headers(owner), mock_minio_download, _alpaca_jsonl())

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)

    response = client.post(
        f"/api/v1/datasets/{dataset['id']}/format", headers=_auth_headers(other_user)
    )

    assert response.status_code == 404


def test_format_dataset_unauthenticated_returns_401(client) -> None:
    response = client.post(f"/api/v1/datasets/{uuid4()}/format")

    assert response.status_code == 401


def test_quality_check_dataset_persists_report(
    client, emails_to_cleanup, mock_minio_upload, mock_minio_download
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    dataset = _upload_dataset(client, headers, mock_minio_download, _alpaca_jsonl())

    response = client.post(f"/api/v1/datasets/{dataset['id']}/quality-check", headers=headers)

    assert response.status_code == 200, response.text
    report = response.json()["quality_report"]
    assert report["total_rows"] == 1
    assert report["unique_rows"] == 1
    assert report["languages"] == {"en": 1}


def test_quality_check_dataset_uses_previously_detected_format(
    client, emails_to_cleanup, mock_minio_upload, mock_minio_download
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    dataset = _upload_dataset(client, headers, mock_minio_download, _alpaca_jsonl())
    client.post(f"/api/v1/datasets/{dataset['id']}/format", headers=headers)

    response = client.post(f"/api/v1/datasets/{dataset['id']}/quality-check", headers=headers)

    assert response.status_code == 200, response.text
    assert response.json()["quality_report"]["total_rows"] == 1


def test_quality_check_dataset_not_found_returns_404(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)

    response = client.post(f"/api/v1/datasets/{uuid4()}/quality-check", headers=_auth_headers(user))

    assert response.status_code == 404


def test_quality_check_dataset_unauthenticated_returns_401(client) -> None:
    response = client.post(f"/api/v1/datasets/{uuid4()}/quality-check")

    assert response.status_code == 401
