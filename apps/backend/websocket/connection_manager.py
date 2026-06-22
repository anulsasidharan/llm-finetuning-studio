"""Tracks active WebSocket connections per training job_id.

A thin in-memory registry — training_hub.py's relay loop writes directly to its own
WebSocket rather than going through ``broadcast`` (each connection holds its own Redis
pub/sub subscription, so routing every message through every socket registered for a
job_id would double-deliver once two clients watch the same job). ``broadcast`` is kept
as a small, independently useful/testable primitive for pushing an arbitrary message to
every client currently watching a job.
"""

from __future__ import annotations

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = {}

    def connect(self, job_id: str, websocket: WebSocket) -> None:
        self._connections.setdefault(job_id, set()).add(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        connections = self._connections.get(job_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            del self._connections[job_id]

    async def broadcast(self, job_id: str, message: str) -> None:
        for websocket in list(self._connections.get(job_id, ())):
            try:
                await websocket.send_text(message)
            except Exception:
                self.disconnect(job_id, websocket)

    def connection_count(self, job_id: str) -> int:
        return len(self._connections.get(job_id, ()))


manager = ConnectionManager()
