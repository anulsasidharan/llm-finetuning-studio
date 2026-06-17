def test_health_returns_200(client) -> None:
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response_body(client) -> None:
    response = client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "LLM Fine-Tuning Studio API"
    assert data["version"] == "1.0.0"
