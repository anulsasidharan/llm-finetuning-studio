"""training_engine's own Celery task — actually runs a fine-tuning job.

Receives everything it needs as task kwargs (job_id, base_model_id, methodology,
training_config, dataset_storage_path, dataset_format) from apps/backend's
tasks.training_tasks.dispatch_training_job via celery.send_task — confirmed PHASE2-009:
never imports apps.backend, matching the standalone-process architecture decision.
Downloads the dataset itself from MinIO (utils/storage.py), picks the right trainer for
the job's methodology, wires utils.callbacks.MetricsCallback (Redis pub/sub, PHASE2-007)
+ utils.gpu_monitor.GPUMonitor (PHASE2-008) + utils.job_status.MetricsPersistCallback
(Postgres snapshots, PHASE2-009) into it, runs train(), and persists the final
status/metrics. ``rlhf`` has no trainer yet (PHASE4-005 stretch goal) — simply absent
from TRAINER_CLASSES, so it falls into the same "no trainer" failure path as any other
unsupported methodology rather than crashing.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import structlog
from trainers.base_trainer import BaseTrainer, TrainerError
from trainers.dpo_trainer import DPOTrainer
from trainers.lora_trainer import LoRATrainer
from trainers.orpo_trainer import ORPOTrainer
from trainers.qlora_trainer import QLoRATrainer
from trainers.sft_trainer import SFTTrainer
from utils.callbacks import MetricsCallback
from utils.gpu_monitor import GPUMonitor
from utils.job_status import (
    MetricsPersistCallback,
    mark_job_completed,
    mark_job_failed,
    mark_job_running,
)
from utils.storage import download_dataset_file
from worker import celery_app

logger = structlog.get_logger()

TRAINER_CLASSES: dict[str, type[BaseTrainer]] = {
    "sft": SFTTrainer,
    "lora": LoRATrainer,
    "qlora": QLoRATrainer,
    "dpo": DPOTrainer,
    "orpo": ORPOTrainer,
}


def _dataset_bucket() -> str:
    return os.environ.get("BUCKET_DATASETS", "fts-datasets")


def _output_dir(job_id: str) -> Path:
    root = os.environ.get("TRAINING_OUTPUT_DIR", "/training_engine/output")
    return Path(root) / job_id


def _parse_dataset_rows(contents: bytes, storage_path: str) -> list[dict[str, Any]]:
    if storage_path.lower().endswith(".jsonl"):
        return [json.loads(line) for line in contents.splitlines() if line.strip()]
    parsed = json.loads(contents)
    return parsed if isinstance(parsed, list) else [parsed]


@celery_app.task(name="training_engine.tasks.run_training_job")
def run_training_job(
    *,
    job_id: str,
    base_model_id: str,
    methodology: str,
    training_config: dict[str, Any],
    dataset_storage_path: str,
    dataset_format: str = "unknown",
) -> dict[str, Any]:
    trainer_cls = TRAINER_CLASSES.get(methodology)
    if trainer_cls is None:
        error = f"No trainer implemented for methodology={methodology!r} yet."
        logger.error("training_job_unsupported_methodology", job_id=job_id, methodology=methodology)
        mark_job_failed(job_id, error)
        return {"status": "failed", "job_id": job_id, "error": error}

    try:
        contents = download_dataset_file(_dataset_bucket(), dataset_storage_path)
        dataset_rows = _parse_dataset_rows(contents, dataset_storage_path)
    except Exception as exc:
        error = f"Failed to load dataset: {exc}"
        logger.exception("training_job_dataset_load_failed", job_id=job_id)
        mark_job_failed(job_id, error)
        return {"status": "failed", "job_id": job_id, "error": error}

    if not dataset_rows:
        error = "Dataset has no rows."
        mark_job_failed(job_id, error)
        return {"status": "failed", "job_id": job_id, "error": error}

    mark_job_running(job_id)

    gpu_monitor = GPUMonitor()
    callbacks = [
        MetricsCallback(job_id=job_id, gpu_monitor=gpu_monitor.sample),
        MetricsPersistCallback(job_id=job_id, gpu_monitor=gpu_monitor.sample),
    ]

    try:
        trainer = trainer_cls(
            job_id=job_id,
            base_model_id=base_model_id,
            methodology=methodology,
            training_config=training_config,
            dataset_rows=dataset_rows,
            output_dir=_output_dir(job_id),
            dataset_format=dataset_format,
            callbacks=callbacks,
        )
        result = trainer.train()
    except TrainerError as exc:
        logger.error("training_job_failed", job_id=job_id, error=str(exc))
        mark_job_failed(job_id, str(exc))
        return {"status": "failed", "job_id": job_id, "error": str(exc)}
    except Exception as exc:  # pragma: no cover - real training failures (OOM, etc.)
        logger.exception("training_job_crashed", job_id=job_id)
        mark_job_failed(job_id, str(exc))
        return {"status": "failed", "job_id": job_id, "error": str(exc)}

    metrics = result.get("metrics", {})
    mark_job_completed(
        job_id, train_loss=metrics.get("train_loss"), eval_loss=metrics.get("eval_loss")
    )
    return result
