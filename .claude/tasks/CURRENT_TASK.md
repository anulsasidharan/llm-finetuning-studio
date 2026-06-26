# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE4-003
## TASK NAME: Email notifications — job complete/failed
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 4, Week 13
## BRANCH: feat/PHASE4-003-email-notifications

## NEXT TASK
PHASE4-004 (Slack notifications — webhook integration).

## SUMMARY (this session, 2026-06-26)
Implemented optional SMTP email notifications when a fine-tune job reaches a terminal
status (`completed` or `failed`).

**Backend files created:**
- `apps/backend/services/email_service.py` — stdlib `smtplib` + `EmailMessage` (STARTTLS);
  no-ops with info log when `SMTP_USER`/`SMTP_PASSWORD` unset.
- `apps/backend/services/notification_service.py` — fetches job + user email via sync
  psycopg2, composes plain-text + HTML body with job metadata and
  `FRONTEND_URL/training/{job_id}` deep link.
- `apps/backend/tasks/notification_tasks.py` — Celery task
  `send_job_status_email` on the `default` queue.

**Backend files modified:**
- `apps/backend/core/config.py` — added `FRONTEND_URL` (default `http://localhost:3000`).
- `apps/backend/core/celery_app.py` — route `tasks.notification_tasks.*` → `default`;
  explicit imports of all `tasks.*` modules so the worker registers them.
- `apps/backend/tasks/training_tasks.py` — `_enqueue_job_status_email` on dispatch-time
  failures (rlhf unsupported, no dataset).

**Training engine files created/modified:**
- `training_engine/utils/notify.py` — `enqueue_job_status_email()` via
  `celery.send_task` by name (cross-process, no apps/backend import).
- `training_engine/utils/job_status.py` — calls `enqueue_job_status_email` from
  `mark_job_completed` and `mark_job_failed`.

**Config:**
- `.env.example` — added `FRONTEND_URL=http://localhost:3000` under Notifications.

**Trigger points:**
1. Training completes or fails in GPU worker → `job_status.mark_job_*` → notify enqueue.
2. Backend dispatch rejects job (rlhf / no dataset) → `training_tasks._mark_job_failed`
   → notify enqueue.

**Verification:**
- `uv run pytest` — backend notification tests 25/25, training_engine notify+job_status 20/20.
- `uv run ruff check` — clean on all touched files.
- No live SMTP send tested (credentials unset in dev — expected no-op path).

## GOTCHAS LOGGED
- Email fires only on `completed`/`failed`, not `queued`/`running`/`pending`.
- SMTP is optional; dev works without credentials (logs `email_skipped_smtp_not_configured`).
- training_engine cannot import apps/backend — uses `utils/notify.py` + `send_task` by name,
  same cross-process pattern as `dispatch_training_job` / `run_training_job`.
- `core/celery_app.py` now eagerly imports all task modules — fixes latent risk that the
  worker wouldn't register tasks unless something else imported them first.
- PHASE4-004 Slack should add a parallel Celery task + hook from the same terminal-status
  points (or a single dispatcher task that fans out to email + Slack).
