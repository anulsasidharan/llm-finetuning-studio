import asyncio
import json
from collections.abc import Iterator
from unittest.mock import AsyncMock
from uuid import uuid4

import psycopg2
import pytest
import websocket.training_hub as training_hub
from core.auth import create_access_token
from core.config import settings
from fastapi import WebSocketDisconnect
from services import job_service
from websocket.connection_manager import manager


def _unique_email() -> str:
    return f"test-ws-{uuid4()}@example.com"


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
def mock_dispatch(monkeypatch) -> None:
    class _FakeDispatch:
        def delay(self, **kwargs) -> None:
            pass

    monkeypatch.setattr(job_service, "dispatch_training_job", _FakeDispatch())


def _register(client, email: str, password: str = "supersecret123") -> dict:
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "WS Tester"},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _auth_headers(user: dict) -> dict:
    access_token = create_access_token({"sub": user["id"]})
    return {"Authorization": f"Bearer {access_token}"}


def _create_job(client, headers: dict) -> dict:
    response = client.post(
        "/api/v1/jobs",
        headers=headers,
        json={
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": {"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


class _FakePubSub:
    def __init__(self, messages: list[dict]) -> None:
        self._messages = list(messages)
        self.subscribed: list[str] = []
        self.unsubscribed: list[str] = []
        self.closed = False

    async def subscribe(self, channel: str) -> None:
        self.subscribed.append(channel)

    async def unsubscribe(self, channel: str) -> None:
        self.unsubscribed.append(channel)

    async def close(self) -> None:
        self.closed = True

    async def listen(self):
        for message in self._messages:
            yield message
        await asyncio.Event().wait()  # simulate real pubsub.listen() blocking for more


class _FakeRedisClient:
    def __init__(self, pubsub: _FakePubSub) -> None:
        self._pubsub = pubsub
        self.closed = False

    def pubsub(self) -> _FakePubSub:
        return self._pubsub

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def fake_redis(monkeypatch):
    def _install(messages: list[dict]) -> tuple[_FakeRedisClient, _FakePubSub]:
        pubsub = _FakePubSub(messages)
        fake_client = _FakeRedisClient(pubsub)
        monkeypatch.setattr(training_hub.redis_asyncio, "from_url", lambda url: fake_client)
        return fake_client, pubsub

    return _install


def test_ws_rejects_connection_without_token(client) -> None:
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(f"/ws/training/{uuid4()}"),
    ):
        pass

    assert exc_info.value.code == training_hub.WS_POLICY_VIOLATION


def test_ws_rejects_connection_with_invalid_token(client) -> None:
    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(f"/ws/training/{uuid4()}?token=not-a-real-token"),
    ):
        pass

    assert exc_info.value.code == training_hub.WS_POLICY_VIOLATION


def test_ws_rejects_connection_for_nonexistent_job(client, emails_to_cleanup) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    token = create_access_token({"sub": user["id"]})

    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(f"/ws/training/{uuid4()}?token={token}"),
    ):
        pass

    assert exc_info.value.code == training_hub.WS_POLICY_VIOLATION


def test_ws_rejects_connection_for_job_not_owned_by_token_user(
    client, emails_to_cleanup, mock_dispatch
) -> None:
    owner_email = _unique_email()
    emails_to_cleanup.append(owner_email)
    owner = _register(client, owner_email)
    job = _create_job(client, _auth_headers(owner))

    other_email = _unique_email()
    emails_to_cleanup.append(other_email)
    other_user = _register(client, other_email)
    other_token = create_access_token({"sub": other_user["id"]})

    with (
        pytest.raises(WebSocketDisconnect) as exc_info,
        client.websocket_connect(f"/ws/training/{job['id']}?token={other_token}"),
    ):
        pass

    assert exc_info.value.code == training_hub.WS_POLICY_VIOLATION


def test_ws_relays_redis_messages_to_owning_client(
    client, emails_to_cleanup, mock_dispatch, fake_redis
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    job = _create_job(client, headers)
    token = create_access_token({"sub": user["id"]})

    metrics_payload = {
        "type": "metrics_update",
        "job_id": job["id"],
        "step": 10,
        "train_loss": 0.42,
    }
    status_payload = {"type": "status_change", "job_id": job["id"], "status": "running"}
    _, pubsub = fake_redis(
        [
            {"type": "subscribe", "data": 1},
            {"type": "message", "data": json.dumps(metrics_payload).encode("utf-8")},
            {"type": "message", "data": json.dumps(status_payload).encode("utf-8")},
        ]
    )

    with client.websocket_connect(f"/ws/training/{job['id']}?token={token}") as ws:
        first = json.loads(ws.receive_text())
        second = json.loads(ws.receive_text())
        assert manager.connection_count(job["id"]) == 1

    assert first == metrics_payload
    assert second == status_payload
    assert pubsub.subscribed == [f"training_metrics:{job['id']}"]


def test_ws_ignores_non_message_pubsub_events(
    client, emails_to_cleanup, mock_dispatch, fake_redis
) -> None:
    email = _unique_email()
    emails_to_cleanup.append(email)
    user = _register(client, email)
    headers = _auth_headers(user)
    job = _create_job(client, headers)
    token = create_access_token({"sub": user["id"]})

    payload = {"type": "metrics_update", "job_id": job["id"], "step": 1}
    fake_redis(
        [
            {"type": "subscribe", "data": 1},
            {"type": "message", "data": json.dumps(payload).encode("utf-8")},
        ]
    )

    with client.websocket_connect(f"/ws/training/{job['id']}?token={token}") as ws:
        received = json.loads(ws.receive_text())

    assert received == payload


def test_serve_relays_message_and_cleans_up_on_disconnect(monkeypatch) -> None:
    """Drives _serve() directly with asyncio.run() instead of TestClient.

    TestClient's websocket teardown cancels the whole ASGI task group as soon as the
    client disconnects, racing ahead of _serve()'s own cleanup awaits (confirmed while
    building this test — see _serve()'s docstring). Calling it directly here, with a
    plain AsyncMock websocket whose receive_text() raises WebSocketDisconnect, gives a
    deterministic single-event-loop run where cleanup is provably reached.
    """
    job_id = uuid4()
    payload = {"type": "metrics_update", "job_id": str(job_id), "step": 1}
    pubsub = _FakePubSub([{"type": "message", "data": json.dumps(payload).encode("utf-8")}])
    fake_client = _FakeRedisClient(pubsub)
    monkeypatch.setattr(training_hub.redis_asyncio, "from_url", lambda url: fake_client)

    ws = AsyncMock()
    ws.receive_text.side_effect = WebSocketDisconnect()

    asyncio.run(training_hub._serve(ws, job_id))

    ws.send_text.assert_awaited_once_with(json.dumps(payload))
    channel = f"training_metrics:{job_id}"
    assert pubsub.subscribed == [channel]
    assert pubsub.unsubscribed == [channel]
    assert pubsub.closed is True
    assert fake_client.closed is True
    assert manager.connection_count(str(job_id)) == 0
