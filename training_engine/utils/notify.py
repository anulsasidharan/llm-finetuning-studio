"""Enqueue backend email notifications for terminal fine-tune job statuses.

training_engine is a standalone process — it cannot import apps/backend. Uses
celery.send_task by name (same broker as apps/backend) to hand off to
``tasks.notification_tasks.send_job_status_email`` on the default queue.
"""

from __future__ import annotations

import os

import structlog

logger = structlog.get_logger()

NOTIFICATION_TASK = "tasks.notification_tasks.send_job_status_email"
DEFAULT_BROKER_URL = "redis://localhost:6380/1"
TERMINAL_STATUSES = frozenset({"completed", "failed"})


def enqueue_job_status_email(*, job_id: str, status: str, error: str | None = None) -> None:
    if status not in TERMINAL_STATUSES:
        return
    try:
        from celery import Celery

        broker = os.environ.get("CELERY_BROKER_URL", DEFAULT_BROKER_URL)
        client = Celery(broker=broker)
        client.send_task(
            NOTIFICATION_TASK,
            kwargs={"job_id": job_id, "status": status, "error": error},
            queue="default",
        )
    except Exception as exc:
        logger.warning(
            "job_notification_enqueue_failed",
            job_id=job_id,
            status=status,
            error=str(exc),
        )
