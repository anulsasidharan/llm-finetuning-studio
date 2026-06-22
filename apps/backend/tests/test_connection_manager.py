import asyncio
from unittest.mock import AsyncMock

from websocket.connection_manager import ConnectionManager


def _fake_websocket() -> AsyncMock:
    return AsyncMock()


def test_connect_tracks_connection_for_job() -> None:
    manager = ConnectionManager()
    ws = _fake_websocket()

    manager.connect("job-1", ws)

    assert manager.connection_count("job-1") == 1


def test_disconnect_removes_connection() -> None:
    manager = ConnectionManager()
    ws = _fake_websocket()
    manager.connect("job-1", ws)

    manager.disconnect("job-1", ws)

    assert manager.connection_count("job-1") == 0


def test_disconnect_unknown_job_is_a_noop() -> None:
    manager = ConnectionManager()

    manager.disconnect("no-such-job", _fake_websocket())  # must not raise

    assert manager.connection_count("no-such-job") == 0


def test_multiple_connections_tracked_independently_per_job() -> None:
    manager = ConnectionManager()
    ws_a, ws_b = _fake_websocket(), _fake_websocket()
    manager.connect("job-1", ws_a)
    manager.connect("job-1", ws_b)
    manager.connect("job-2", _fake_websocket())

    assert manager.connection_count("job-1") == 2
    assert manager.connection_count("job-2") == 1


def test_broadcast_sends_to_every_connection_for_job() -> None:
    manager = ConnectionManager()
    ws_a, ws_b = _fake_websocket(), _fake_websocket()
    manager.connect("job-1", ws_a)
    manager.connect("job-1", ws_b)

    asyncio.run(manager.broadcast("job-1", "hello"))

    ws_a.send_text.assert_awaited_once_with("hello")
    ws_b.send_text.assert_awaited_once_with("hello")


def test_broadcast_drops_connection_that_fails_to_send() -> None:
    manager = ConnectionManager()
    ws_ok, ws_broken = _fake_websocket(), _fake_websocket()
    ws_broken.send_text.side_effect = RuntimeError("connection closed")
    manager.connect("job-1", ws_ok)
    manager.connect("job-1", ws_broken)

    asyncio.run(manager.broadcast("job-1", "hello"))

    assert manager.connection_count("job-1") == 1
