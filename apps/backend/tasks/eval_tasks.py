"""Celery task that dispatches a created EvalJob to training_engine's own worker.

Mirrors tasks/training_tasks.py's dispatch_training_job: training_engine runs as its
own standalone Celery worker process (separate venv/container, never imported into
apps/backend, since apps/backend/requirements.txt has none of the heavy ML deps
torch/transformers/lm-eval-harness needs). This task stays on the backend's own Celery
app/broker (queue "training") and only does lightweight work: flip the job to "queued",
then hand off to training_engine by task name via celery.send_task -- no training_engine
import here at all.
"""

from __future__ import annotations

from typing import Any

import structlog
from core.celery_app import celery
from core.config import settings

logger = structlog.get_logger()


def _connect() -> Any:
    import psycopg2

    return psycopg2.connect(settings.DATABASE_URL_SYNC)


def _update_eval_status(eval_id: str, status: str) -> None:
    conn = _connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE eval_jobs SET status = %(status)s WHERE id = %(eval_id)s",
                {"status": status, "eval_id": eval_id},
            )
    finally:
        conn.close()


@celery.task(name="tasks.eval_tasks.dispatch_eval_job")
def dispatch_eval_job(
    *,
    eval_id: str,
    eval_type: str,
    base_model_id: str,
    finetuned_model_id: str | None,
    prompts: list[str] | None,
    benchmarks: list[str] | None,
    max_new_tokens: int | None,
    num_fewshot: int | None,
    sample_limit: float | None,
) -> None:
    _update_eval_status(eval_id, "queued")

    celery.send_task(
        "training_engine.tasks.run_eval_job",
        kwargs={
            "eval_id": eval_id,
            "eval_type": eval_type,
            "base_model_id": base_model_id,
            "finetuned_model_id": finetuned_model_id,
            "prompts": prompts,
            "benchmarks": benchmarks,
            "max_new_tokens": max_new_tokens,
            "num_fewshot": num_fewshot,
            "sample_limit": sample_limit,
        },
        queue="gpu_training",
    )
