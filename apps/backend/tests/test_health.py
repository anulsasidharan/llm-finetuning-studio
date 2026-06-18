from unittest.mock import AsyncMock, patch


def test_health_returns_200(client) -> None:
    with (
        patch("main._check_database", new=AsyncMock(return_value="up")),
        patch("main._check_redis", new=AsyncMock(return_value="up")),
        patch("main._check_storage", new=AsyncMock(return_value="up")),
    ):
        response = client.get("/health")
    assert response.status_code == 200


def test_health_response_body_all_up(client) -> None:
    with (
        patch("main._check_database", new=AsyncMock(return_value="up")),
        patch("main._check_redis", new=AsyncMock(return_value="up")),
        patch("main._check_storage", new=AsyncMock(return_value="up")),
    ):
        response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "LLM Fine-Tuning Studio API"
    assert data["version"] == "1.0.0"
    assert data["database"] == "up"
    assert data["redis"] == "up"
    assert data["storage"] == "up"


def test_health_response_body_degraded_when_dependency_down(client) -> None:
    with (
        patch("main._check_database", new=AsyncMock(return_value="down")),
        patch("main._check_redis", new=AsyncMock(return_value="up")),
        patch("main._check_storage", new=AsyncMock(return_value="up")),
    ):
        response = client.get("/health")
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] == "down"
    assert response.status_code == 200


def test_health_database_check_failure_reports_down() -> None:
    import asyncio

    from main import _check_database

    with patch("main.AsyncSessionLocal", side_effect=RuntimeError("connection refused")):
        result = asyncio.run(_check_database())
    assert result == "down"


def test_health_redis_check_failure_reports_down() -> None:
    import asyncio

    from main import _check_redis

    with patch("main.redis_asyncio.from_url", side_effect=RuntimeError("connection refused")):
        result = asyncio.run(_check_redis())
    assert result == "down"


def test_health_storage_check_failure_reports_down() -> None:
    import asyncio

    from main import _check_storage

    with patch("main.minio_client.bucket_exists", side_effect=RuntimeError("connection refused")):
        result = asyncio.run(_check_storage())
    assert result == "down"
