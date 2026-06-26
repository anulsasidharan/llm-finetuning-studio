"""Celery tasks that dispatch export operations to training_engine's GPU worker.

Mirrors tasks/eval_tasks.py's dispatch pattern: lightweight backend tasks that flip
registry state, then hand off to training_engine via celery.send_task (no import of
training_engine in apps/backend — confirmed standalone-process architecture decision).
"""

from __future__ import annotations

import structlog
from core.celery_app import celery
from core.config import settings

logger = structlog.get_logger()


def _connect():  # type: ignore[return]
    import psycopg2

    return psycopg2.connect(settings.DATABASE_URL_SYNC)


@celery.task(name="tasks.export_tasks.dispatch_push_hf")
def dispatch_push_hf(
    *,
    registry_id: str,
    storage_path: str,
    hf_repo_id: str,
    hf_token: str,
    private: bool,
) -> None:
    celery.send_task(
        "training_engine.tasks.run_export_job",
        kwargs={
            "registry_id": registry_id,
            "export_type": "push_hf",
            "storage_path": storage_path,
            "hf_repo_id": hf_repo_id,
            "hf_token": hf_token,
            "private": private,
        },
        queue="gpu_training",
    )


@celery.task(name="tasks.export_tasks.dispatch_export_gguf")
def dispatch_export_gguf(
    *,
    registry_id: str,
    storage_path: str,
    quantization_type: str,
) -> None:
    celery.send_task(
        "training_engine.tasks.run_export_job",
        kwargs={
            "registry_id": registry_id,
            "export_type": "export_gguf",
            "storage_path": storage_path,
            "quantization_type": quantization_type,
        },
        queue="gpu_training",
    )
