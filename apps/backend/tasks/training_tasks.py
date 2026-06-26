"""Celery task that dispatches a created FineTuneJob to training_engine's own worker.

Confirmed PHASE2-009: training_engine runs as its own standalone Celery worker process
(separate venv/container, matches docker-compose.gpu.yml's existing
``celery -A worker.celery_app worker --queues=gpu_training`` command) rather than being
imported into apps/backend — apps/backend/requirements.txt has none of the heavy ML
deps (torch/transformers/trl/peft/bitsandbytes) training_engine needs. This task stays
on the backend's own Celery app/broker (queue "training", per core/celery_app.py's
existing task_routes) and only does lightweight work: reject unsupported
methodologies early, flip the job to "queued", then hand off to training_engine by
task name via celery.send_task (no training_engine import here at all) so
training_engine can download the dataset itself from MinIO and run training.
"""

from __future__ import annotations

import json
from typing import Any

import redis
import structlog
from core.celery_app import celery
from core.config import settings

logger = structlog.get_logger()

UNSUPPORTED_METHODOLOGIES = frozenset({"rlhf"})

DEFAULT_PUBSUB_REDIS_URL = "redis://localhost:6380/3"


def _connect() -> Any:
    import psycopg2

    return psycopg2.connect(settings.DATABASE_URL_SYNC)


def _update_job_status(job_id: str, status: str) -> None:
    conn = _connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE fine_tune_jobs SET status = %(status)s WHERE id = %(job_id)s",
                {"status": status, "job_id": job_id},
            )
    finally:
        conn.close()


def _publish_status_change(job_id: str, status: str) -> None:
    """Publish a status_change event so a connected WS client sees this live.

    Mirrors training_engine/utils/callbacks.py's ``publish_status_change`` — apps/backend
    can't import training_engine (standalone-process architecture decision), so this is
    a small duplicate using the same channel/payload shape and the same
    ``TRAINING_PUBSUB_DB`` Redis URL the WebSocket hub subscribes through.
    """
    try:
        client = redis.Redis.from_url(settings.TRAINING_PUBSUB_DB or DEFAULT_PUBSUB_REDIS_URL)
        client.publish(
            f"training_metrics:{job_id}",
            json.dumps({"type": "status_change", "job_id": job_id, "status": status}),
        )
    except Exception as exc:
        logger.warning("status_change_publish_failed", job_id=job_id, status=status, error=str(exc))


def _mark_job_queued(job_id: str) -> None:
    _update_job_status(job_id, "queued")
    _publish_status_change(job_id, "queued")


def _enqueue_job_status_email(job_id: str, status: str, error: str | None = None) -> None:
    try:
        celery.send_task(
            "tasks.notification_tasks.send_job_status_email",
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


def _mark_job_failed(job_id: str, error: str) -> None:
    logger.error("training_dispatch_failed", job_id=job_id, error=error)
    _update_job_status(job_id, "failed")
    _publish_status_change(job_id, "failed")
    _enqueue_job_status_email(job_id, "failed", error=error)


@celery.task(name="tasks.training_tasks.dispatch_training_job")
def dispatch_training_job(
    *,
    job_id: str,
    base_model_id: str,
    methodology: str,
    training_config: dict[str, Any],
    dataset_storage_path: str | None,
    dataset_format: str | None,
) -> None:
    if methodology in UNSUPPORTED_METHODOLOGIES:
        _mark_job_failed(job_id, f"No trainer implemented for methodology={methodology!r} yet.")
        return

    if dataset_storage_path is None:
        _mark_job_failed(job_id, "Job has no dataset attached.")
        return

    _mark_job_queued(job_id)

    celery.send_task(
        "training_engine.tasks.run_training_job",
        kwargs={
            "job_id": job_id,
            "base_model_id": base_model_id,
            "methodology": methodology,
            "training_config": training_config,
            "dataset_storage_path": dataset_storage_path,
            "dataset_format": dataset_format or "unknown",
        },
        queue="gpu_training",
    )
