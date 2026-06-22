"""MetricsCallback — publishes live training metrics to Redis pub/sub.

Channel naming follows the contract already documented in the repo's
MEMORY.md WEBSOCKET PATTERN section (written ahead of this callback landing):
``training_metrics:{job_id}``. The planned WebSocket hub (PHASE2-010)
subscribes to this exact channel name to relay updates to the browser.

Payload ``type`` is always ``"metrics_update"`` here — the sibling
``"status_change"`` type belongs to whatever marks job status transitions
(the Celery task wrapping a trainer), not this callback. That's
``publish_status_change`` below, called from ``utils/job_status.py``'s
``mark_job_running``/``mark_job_completed``/``mark_job_failed`` (PHASE2-010), so a
WebSocket client connected to ``WS /ws/training/{job_id}`` sees status flips live, not
just metric updates.
"""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from typing import Any

import redis
import structlog
from transformers import TrainerCallback, TrainerControl, TrainerState, TrainingArguments

logger = structlog.get_logger()

DEFAULT_REDIS_URL = "redis://localhost:6380/3"


def _default_redis_url() -> str:
    """Read the dedicated training_engine Redis URL.

    ``TRAINING_ENGINE_REDIS_URL`` is already declared in .env.example
    (db index 3, separate from the backend's db 0) — training_engine is a
    standalone process per CLAUDE.md's architecture decision and does not
    import apps/backend/core/config.py. The fallback targets the host-mapped
    port (localhost:6380) confirmed in MEMORY.md's PORT MAP for running
    outside Docker.
    """
    return os.environ.get("TRAINING_ENGINE_REDIS_URL", DEFAULT_REDIS_URL)


class MetricsCallback(TrainerCallback):
    """Publish train/eval metrics to Redis pub/sub during a HF/TRL training run.

    Hooks ``on_log`` (fired every ``logging_steps``, see
    ``BaseTrainer.build_training_arguments``) and ``on_evaluate`` — not
    ``on_step_end``, which fires every single step and would flood Redis far
    more often than the metrics actually change.

    Callers (the future Celery training task) construct this explicitly and
    pass it via the existing ``BaseTrainer(..., callbacks=[...])`` kwarg —
    ``BaseTrainer.get_callbacks()`` itself stays caller-injected, not
    auto-wired, consistent with how ``dataset_rows`` and every other
    external dependency is already threaded into trainers.
    """

    def __init__(
        self,
        *,
        job_id: str,
        redis_url: str | None = None,
        redis_client: Any = None,
        gpu_monitor: Callable[[], dict[str, Any]] | None = None,
        channel: str | None = None,
    ) -> None:
        self.job_id = str(job_id)
        self.redis_url = redis_url or _default_redis_url()
        self.channel = channel or f"training_metrics:{self.job_id}"
        self._gpu_monitor = gpu_monitor
        self._client = redis_client

    def _get_redis_client(self) -> Any:
        if self._client is None:
            self._client = redis.Redis.from_url(self.redis_url)
        return self._client

    def _gpu_stats(self) -> dict[str, Any]:
        if self._gpu_monitor is None:
            return {}
        return self._gpu_monitor()

    def _build_payload(
        self,
        *,
        step: int,
        epoch: float | None,
        train_loss: float | None = None,
        eval_loss: float | None = None,
        tokens_per_second: float | None = None,
    ) -> dict[str, Any]:
        gpu_stats = self._gpu_stats()
        return {
            "type": "metrics_update",
            "job_id": self.job_id,
            "step": step,
            "epoch": epoch,
            "train_loss": train_loss,
            "eval_loss": eval_loss,
            "gpu_utilization_pct": gpu_stats.get("gpu_utilization_pct"),
            "vram_used_gb": gpu_stats.get("vram_used_gb"),
            "tokens_per_second": tokens_per_second,
        }

    def _publish(self, payload: dict[str, Any]) -> None:
        try:
            client = self._get_redis_client()
            client.publish(self.channel, json.dumps(payload))
        except Exception as exc:
            logger.warning(
                "metrics_callback_publish_failed",
                job_id=self.job_id,
                channel=self.channel,
                error=str(exc),
            )

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
        payload = self._build_payload(
            step=state.global_step,
            epoch=logs.get("epoch", state.epoch),
            train_loss=train_loss,
            eval_loss=eval_loss,
            tokens_per_second=logs.get("train_tokens_per_second"),
        )
        self._publish(payload)

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
        payload = self._build_payload(
            step=state.global_step, epoch=state.epoch, eval_loss=eval_loss
        )
        self._publish(payload)


def publish_status_change(
    *,
    job_id: str,
    status: str,
    redis_client: Any = None,
    redis_url: str | None = None,
    channel: str | None = None,
) -> None:
    """Publish a ``status_change`` event to the same channel ``MetricsCallback`` uses.

    Standalone function rather than a method on ``MetricsCallback`` — status
    transitions are marked by ``utils/job_status.py``, not by a ``TrainerCallback``
    hook, so there's no shared instance to hang this off of. Publish failures are
    caught and logged here too, same risk tolerance as ``MetricsCallback._publish``
    (a transient Redis outage must not crash a job-status update).
    """
    job_id = str(job_id)
    channel = channel or f"training_metrics:{job_id}"
    payload = {"type": "status_change", "job_id": job_id, "status": status}
    try:
        client = redis_client or redis.Redis.from_url(redis_url or _default_redis_url())
        client.publish(channel, json.dumps(payload))
    except Exception as exc:
        logger.warning("status_change_publish_failed", job_id=job_id, status=status, error=str(exc))
