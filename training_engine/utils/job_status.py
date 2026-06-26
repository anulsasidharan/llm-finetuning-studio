"""Sync Postgres writes for FineTuneJob status/metrics — training_engine's own DB access.

training_engine is a standalone process (CLAUDE.md architecture decision) and does not
import apps/backend/models or core/database.py — confirmed PHASE2-009: it talks to the
same ``fine_tune_jobs`` table directly over a sync psycopg2 connection using raw SQL.
Reads ``DATABASE_URL_SYNC`` straight from the environment (same pattern as
``utils/callbacks.py``'s ``TRAINING_ENGINE_REDIS_URL`` lookup) since training_engine has
no pydantic-settings config layer. The user explicitly chose "coarse status + periodic
metric snapshots" over Redis/WebSocket-only metrics (PHASE2-009 decision) — so
``MetricsPersistCallback`` here writes the same train_loss/eval_loss/gpu_utilization_pct/
vram_used_gb/tokens_per_second columns ``utils/callbacks.py``'s ``MetricsCallback``
publishes to Redis pub/sub, on the same ``on_log``/``on_evaluate`` hooks, but to Postgres
instead — kept as a separate class so ``MetricsCallback`` itself stays Redis-only per its
own PHASE2-007 docstring.
"""

from __future__ import annotations

import os
from typing import Any

import structlog
from transformers import TrainerCallback, TrainerControl, TrainerState, TrainingArguments

from utils.callbacks import publish_status_change
from utils.notify import enqueue_job_status_notifications

logger = structlog.get_logger()

DEFAULT_DATABASE_URL_SYNC = (
    "postgresql://fts_user:fts_password_change_in_production@localhost:5433/fts_db"
)


def _database_url() -> str:
    return os.environ.get("DATABASE_URL_SYNC", DEFAULT_DATABASE_URL_SYNC)


def _connect() -> Any:
    import psycopg2

    return psycopg2.connect(_database_url())


def _execute(query: str, params: dict[str, Any]) -> None:
    conn = _connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(query, params)
    finally:
        conn.close()


def mark_job_running(job_id: str) -> None:
    try:
        _execute(
            "UPDATE fine_tune_jobs SET status = %(status)s WHERE id = %(job_id)s",
            {"status": "running", "job_id": job_id},
        )
    except Exception as exc:
        logger.warning("job_status_update_failed", job_id=job_id, status="running", error=str(exc))
    publish_status_change(job_id=job_id, status="running")


def mark_job_completed(
    job_id: str, *, train_loss: float | None = None, eval_loss: float | None = None
) -> None:
    try:
        _execute(
            "UPDATE fine_tune_jobs SET status = %(status)s, train_loss = %(train_loss)s, "
            "eval_loss = %(eval_loss)s WHERE id = %(job_id)s",
            {
                "status": "completed",
                "train_loss": train_loss,
                "eval_loss": eval_loss,
                "job_id": job_id,
            },
        )
    except Exception as exc:
        logger.warning(
            "job_status_update_failed", job_id=job_id, status="completed", error=str(exc)
        )
    publish_status_change(job_id=job_id, status="completed")
    enqueue_job_status_notifications(job_id=job_id, status="completed")


def mark_job_failed(job_id: str, error: str) -> None:
    logger.error("training_job_failed", job_id=job_id, error=error)
    try:
        _execute(
            "UPDATE fine_tune_jobs SET status = %(status)s WHERE id = %(job_id)s",
            {"status": "failed", "job_id": job_id},
        )
    except Exception as exc:
        logger.warning("job_status_update_failed", job_id=job_id, status="failed", error=str(exc))
    publish_status_change(job_id=job_id, status="failed")
    enqueue_job_status_notifications(job_id=job_id, status="failed", error=error)


def update_job_metrics(
    job_id: str,
    *,
    train_loss: float | None = None,
    eval_loss: float | None = None,
    gpu_utilization_pct: float | None = None,
    vram_used_gb: float | None = None,
    tokens_per_second: float | None = None,
) -> None:
    try:
        _execute(
            """
            UPDATE fine_tune_jobs SET
                train_loss = COALESCE(%(train_loss)s, train_loss),
                eval_loss = COALESCE(%(eval_loss)s, eval_loss),
                gpu_utilization_pct = COALESCE(%(gpu_utilization_pct)s, gpu_utilization_pct),
                vram_used_gb = COALESCE(%(vram_used_gb)s, vram_used_gb),
                tokens_per_second = COALESCE(%(tokens_per_second)s, tokens_per_second)
            WHERE id = %(job_id)s
            """,
            {
                "train_loss": train_loss,
                "eval_loss": eval_loss,
                "gpu_utilization_pct": gpu_utilization_pct,
                "vram_used_gb": vram_used_gb,
                "tokens_per_second": tokens_per_second,
                "job_id": job_id,
            },
        )
    except Exception as exc:
        logger.warning("job_metrics_update_failed", job_id=job_id, error=str(exc))


class MetricsPersistCallback(TrainerCallback):
    """Persist periodic train/eval metric snapshots to Postgres during a training run.

    Mirrors ``utils.callbacks.MetricsCallback``'s ``on_log``/``on_evaluate`` hook shape
    (same fields, same "every logging_steps, not every step" cadence) but writes to the
    ``fine_tune_jobs`` row instead of publishing to Redis. Accepts the same
    ``gpu_monitor`` zero-arg callable contract as ``MetricsCallback`` so
    ``GPUMonitor().sample`` drops into both without an adapter.
    """

    def __init__(
        self,
        *,
        job_id: str,
        gpu_monitor: Any = None,
    ) -> None:
        self.job_id = str(job_id)
        self._gpu_monitor = gpu_monitor

    def _gpu_stats(self) -> dict[str, Any]:
        if self._gpu_monitor is None:
            return {}
        return self._gpu_monitor()

    def on_log(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        logs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if not logs:
            return
        train_loss = logs.get("loss")
        eval_loss = logs.get("eval_loss")
        if train_loss is None and eval_loss is None:
            return
        gpu_stats = self._gpu_stats()
        update_job_metrics(
            self.job_id,
            train_loss=train_loss,
            eval_loss=eval_loss,
            gpu_utilization_pct=gpu_stats.get("gpu_utilization_pct"),
            vram_used_gb=gpu_stats.get("vram_used_gb"),
            tokens_per_second=logs.get("train_tokens_per_second"),
        )

    def on_evaluate(
        self,
        args: TrainingArguments,
        state: TrainerState,
        control: TrainerControl,
        metrics: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        if not metrics:
            return
        eval_loss = metrics.get("eval_loss")
        if eval_loss is None:
            return
        update_job_metrics(self.job_id, eval_loss=eval_loss)
