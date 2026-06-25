"""Sync Postgres writes for EvalJob status/result -- training_engine's own DB access.

Mirrors utils/job_status.py's pattern for fine_tune_jobs: training_engine is a
standalone process (CLAUDE.md architecture decision) and talks to the same
``eval_jobs`` table directly over a sync psycopg2 connection using raw SQL, reading
``DATABASE_URL_SYNC`` straight from the environment. No Redis pub/sub here -- unlike
training jobs, eval jobs have no WebSocket hub consumer; the frontend polls
GET /eval/{eval_id} instead, so there's nothing to publish to.
"""

from __future__ import annotations

import json
import os
from typing import Any

import structlog

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


def mark_eval_running(eval_id: str) -> None:
    try:
        _execute(
            "UPDATE eval_jobs SET status = %(status)s WHERE id = %(eval_id)s",
            {"status": "running", "eval_id": eval_id},
        )
    except Exception as exc:
        logger.warning(
            "eval_status_update_failed", eval_id=eval_id, status="running", error=str(exc)
        )


def mark_eval_completed(eval_id: str, result: dict[str, Any]) -> None:
    try:
        _execute(
            "UPDATE eval_jobs SET status = %(status)s, result = %(result)s WHERE id = %(eval_id)s",
            {"status": "completed", "result": json.dumps(result), "eval_id": eval_id},
        )
    except Exception as exc:
        logger.warning(
            "eval_status_update_failed", eval_id=eval_id, status="completed", error=str(exc)
        )


def mark_eval_failed(eval_id: str, error: str) -> None:
    logger.error("eval_job_failed", eval_id=eval_id, error=error)
    try:
        _execute(
            "UPDATE eval_jobs SET status = %(status)s, error_message = %(error)s "
            "WHERE id = %(eval_id)s",
            {"status": "failed", "error": error, "eval_id": eval_id},
        )
    except Exception as exc:
        logger.warning(
            "eval_status_update_failed", eval_id=eval_id, status="failed", error=str(exc)
        )
