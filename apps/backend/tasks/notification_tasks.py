"""Celery tasks for outbound notifications — routed to the default queue."""

from __future__ import annotations

import structlog
from core.celery_app import celery
from services.notification_service import deliver_job_status_email

logger = structlog.get_logger()


@celery.task(name="tasks.notification_tasks.send_job_status_email")
def send_job_status_email(*, job_id: str, status: str, error: str | None = None) -> None:
    try:
        deliver_job_status_email(job_id=job_id, status=status, error=error)
    except Exception as exc:
        logger.error(
            "job_status_email_failed",
            job_id=job_id,
            status=status,
            error=str(exc),
        )
