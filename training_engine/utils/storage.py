"""Minimal MinIO client for training_engine's own dataset downloads.

training_engine is a standalone process (CLAUDE.md architecture decision) and does not
import apps/backend/core/storage.py — confirmed PHASE2-009: it builds its own MinIO
client, reading the same MINIO_* env vars (shared via docker-compose.gpu.yml's
``env_file: .env``) directly via ``os.environ``, since training_engine has no
pydantic-settings config layer (same pattern as ``utils/callbacks.py``'s
``TRAINING_ENGINE_REDIS_URL`` / ``utils/job_status.py``'s ``DATABASE_URL_SYNC``).
``minio`` is lazily imported for testability, mirroring the lazy-import pattern used
throughout training_engine (e.g. ``qlora_trainer.py``'s ``_get_bitsandbytes_config_cls``).
"""

from __future__ import annotations

import os
from typing import Any


def _get_minio_client() -> Any:
    from minio import Minio

    return Minio(
        f"{os.environ.get('MINIO_HOST', 'minio')}:{os.environ.get('MINIO_PORT', '9000')}",
        access_key=os.environ.get("MINIO_ROOT_USER", "minioadmin"),
        secret_key=os.environ.get("MINIO_ROOT_PASSWORD", ""),
        secure=os.environ.get("MINIO_USE_SSL", "false").lower() == "true",
    )


def download_dataset_file(bucket: str, object_name: str) -> bytes:
    client = _get_minio_client()
    response = client.get_object(bucket, object_name)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()
