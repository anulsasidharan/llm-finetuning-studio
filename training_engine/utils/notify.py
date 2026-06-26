"""Enqueue backend notifications for terminal fine-tune job statuses.

training_engine is a standalone process — it cannot import apps/backend. Uses
celery.send_task by name (same broker as apps/backend) to hand off to
``tasks.notification_tasks`` on the default queue.
"""

from __future__ import annotations

import os

import structlog

logger = structlog.get_logger()

EMAIL_NOTIFICATION_TASK = "tasks.notification_tasks.send_job_status_email"
SLACK_NOTIFICATION_TASK = "tasks.notification_tasks.send_job_status_slack"
DEFAULT_BROKER_URL = "redis://localhost:6380/1"
TERMINAL_STATUSES = frozenset({"completed", "failed"})


def _send_notification_task(
    task_name: str,
    *,
    job_id: str,
    status: str,
    error: str | None = None,
) -> None:
    from celery import Celery

    broker = os.environ.get("CELERY_BROKER_URL", DEFAULT_BROKER_URL)
    client = Celery(broker=broker)
    client.send_task(
        task_name,
        kwargs={"job_id": job_id, "status": status, "error": error},
        queue="default",
    )


def enqueue_job_status_email(*, job_id: str, status: str, error: str | None = None) -> None:
    if status not in TERMINAL_STATUSES:
        return
    try:
        _send_notification_task(
            EMAIL_NOTIFICATION_TASK,
            job_id=job_id,
            status=status,
            error=error,
        )
    except Exception as exc:
        logger.warning(
            "job_notification_enqueue_failed",
            channel="email",
            job_id=job_id,
            status=status,
            error=str(exc),
        )


def enqueue_job_status_slack(*, job_id: str, status: str, error: str | None = None) -> None:
    if status not in TERMINAL_STATUSES:
        return
    try:
        _send_notification_task(
            SLACK_NOTIFICATION_TASK,
            job_id=job_id,
            status=status,
            error=error,
        )
    except Exception as exc:
        logger.warning(
            "job_notification_enqueue_failed",
            channel="slack",
            job_id=job_id,
            status=status,
            error=str(exc),
        )


def enqueue_job_status_notifications(*, job_id: str, status: str, error: str | None = None) -> None:
    enqueue_job_status_email(job_id=job_id, status=status, error=error)
    enqueue_job_status_slack(job_id=job_id, status=status, error=error)
