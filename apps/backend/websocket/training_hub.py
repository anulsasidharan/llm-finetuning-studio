"""WS /ws/training/{job_id} — relays live training metrics from Redis to the browser.

Subscribes to the Redis pub/sub channel ``training_metrics:{job_id}`` (published by
training_engine/utils/callbacks.py's MetricsCallback for ``metrics_update`` payloads,
PHASE2-007, and training_engine/tasks.py for ``status_change`` payloads, PHASE2-010) and
forwards every message verbatim to the connected client as a WebSocket text frame.

Auth: WebSocket clients cannot send an Authorization header, so the access token is
passed as a query param (``?token=...``) and verified with the same
``core.auth.decode_token`` REST routes already use, then the job is loaded scoped to
that user — same ownership check as ``services.job_service.get_job``, done by hand here
since that helper takes an ``AsyncSession`` the way ``Depends(get_db)`` provides it to
REST routes, which a WebSocket route doesn't get the same way. Any failure
(missing/invalid token, job not found, job not owned by that user) closes the connection
with code 1008 (policy violation) *before* accepting it.
"""

from __future__ import annotations

import asyncio
from uuid import UUID

import redis.asyncio as redis_asyncio
import structlog
from core.auth import decode_token
from core.config import settings
from core.database import AsyncSessionLocal
from fastapi import APIRouter, HTTPException, Query, WebSocket
from models.fine_tune_job import FineTuneJob
from sqlalchemy import select

from websocket.connection_manager import manager

logger = structlog.get_logger()

router = APIRouter()

WS_POLICY_VIOLATION = 1008
DEFAULT_PUBSUB_REDIS_URL = "redis://localhost:6380/3"


def _pubsub_redis_url() -> str:
    return settings.TRAINING_PUBSUB_DB or DEFAULT_PUBSUB_REDIS_URL


async def _is_authorized(token: str | None, job_id: UUID) -> bool:
    if not token:
        return False
    try:
        payload = decode_token(token)
    except HTTPException:
        return False

    user_id = payload.get("sub")
    if user_id is None:
        return False
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return False

    async with AsyncSessionLocal() as db:
        job = await db.scalar(
            select(FineTuneJob).where(FineTuneJob.id == job_id, FineTuneJob.user_id == user_uuid)
        )
    return job is not None


@router.websocket("/ws/training/{job_id}")
async def training_metrics_ws(
    websocket: WebSocket, job_id: UUID, token: str | None = Query(default=None)
) -> None:
    if not await _is_authorized(token, job_id):
        await websocket.close(code=WS_POLICY_VIOLATION)
        return

    await websocket.accept()
    await _serve(websocket, job_id)


async def _serve(websocket: WebSocket, job_id: UUID) -> None:
    """Relay Redis pub/sub messages to ``websocket`` until it disconnects.

    Split out from the route handler itself (which only does auth + accept) so it can
    be exercised directly in a unit test with a fake WebSocket/Redis pair — the real
    disconnect path can't be reliably driven through FastAPI's ``TestClient``, whose
    WebSocket teardown cancels the whole ASGI task group as soon as the client closes,
    racing ahead of this function's own cleanup ``await``s.
    """
    job_id_str = str(job_id)
    manager.connect(job_id_str, websocket)

    channel = f"training_metrics:{job_id_str}"
    redis_client = redis_asyncio.from_url(_pubsub_redis_url())
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)

    async def _relay() -> None:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue
            data = message["data"]
            if isinstance(data, bytes):
                data = data.decode("utf-8")
            await websocket.send_text(data)

    async def _watch_disconnect() -> None:
        while True:
            await websocket.receive_text()

    relay_task = asyncio.create_task(_relay())
    watch_task = asyncio.create_task(_watch_disconnect())

    try:
        await asyncio.wait({relay_task, watch_task}, return_when=asyncio.FIRST_COMPLETED)
    finally:
        relay_task.cancel()
        watch_task.cancel()
        await asyncio.gather(relay_task, watch_task, return_exceptions=True)
        manager.disconnect(job_id_str, websocket)
        try:
            await pubsub.unsubscribe(channel)
            await pubsub.close()
        except Exception as exc:
            logger.warning("training_hub_pubsub_cleanup_failed", job_id=job_id_str, error=str(exc))
        await redis_client.close()
