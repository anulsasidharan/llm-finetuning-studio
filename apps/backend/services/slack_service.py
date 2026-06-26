"""Slack incoming-webhook delivery — optional when SLACK_WEBHOOK_URL is unset."""

from __future__ import annotations

from typing import Any

import httpx
import structlog
from core.config import settings

logger = structlog.get_logger()


def slack_configured() -> bool:
    return bool(settings.SLACK_WEBHOOK_URL)


def post_slack_message(
    *,
    text: str,
    blocks: list[dict[str, Any]] | None = None,
    client: httpx.Client | None = None,
) -> None:
    if not slack_configured():
        logger.info("slack_skipped_webhook_not_configured")
        return

    payload: dict[str, Any] = {"text": text}
    if blocks is not None:
        payload["blocks"] = blocks

    http_client = client or httpx.Client(timeout=15.0)
    owns_client = client is None
    try:
        response = http_client.post(settings.SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.error("slack_post_failed", error=str(exc))
        raise
    finally:
        if owns_client:
            http_client.close()

    logger.info("slack_message_posted")
