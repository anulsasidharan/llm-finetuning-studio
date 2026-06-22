"""Celery app for training_engine's own standalone GPU worker process.

Separate from apps/backend/core/celery_app.py — confirmed PHASE2-009: training_engine
runs as its own Celery worker (matches docker-compose.gpu.yml's existing
``celery -A worker.celery_app worker --queues=gpu_training`` command), never imported
into apps/backend. The backend's tasks.training_tasks.dispatch_training_job hands work
off here by task name via celery.send_task — no shared Python import between the two
processes. Reads CELERY_BROKER_URL/CELERY_RESULT_BACKEND straight from the environment
(same .env shared via docker-compose.gpu.yml's env_file, no pydantic-settings layer
here) following the established pattern in utils/callbacks.py's
TRAINING_ENGINE_REDIS_URL lookup.
"""

from __future__ import annotations

import os

from celery import Celery

celery_app = Celery(
    "training_engine",
    broker=os.environ.get("CELERY_BROKER_URL", "redis://localhost:6380/1"),
    backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://localhost:6380/2"),
    include=["tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_default_queue="gpu_training",
)
