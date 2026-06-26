# CURRENT TASK
# Claude Code reads this at the start of every session.
# Replace contents when moving to a new task.

## TASK ID: PHASE4-004
## TASK NAME: Slack notifications — webhook integration
## STATUS: ✅ DONE
## ASSIGNED PHASE: Phase 4, Week 13
## BRANCH: feat/PHASE4-004-slack-notifications

## NEXT TASK
PHASE4-005 (RLHF support — PPOTrainer + RewardTrainer, stretch goal).

## SUMMARY (this session, 2026-06-26)
Implemented optional Slack incoming-webhook notifications when a fine-tune job reaches a
terminal status (`completed` or `failed`), fanning out alongside email from the same hooks.

**Backend files created:**
- `apps/backend/services/slack_service.py` — sync `httpx.Client` POST to
  `SLACK_WEBHOOK_URL`; no-ops with info log when webhook unset.

**Backend files modified:**
- `apps/backend/services/notification_service.py` — `_build_slack_text()` /
  `_build_slack_blocks()` (Block Kit header, fields, dashboard button) +
  `deliver_job_status_slack()` reusing `JobNotificationContext`.
- `apps/backend/tasks/notification_tasks.py` — Celery task
  `send_job_status_slack` on the `default` queue.
- `apps/backend/tasks/training_tasks.py` — `_enqueue_job_status_notifications()`
  fans out email + Slack Celery tasks (replaces `_enqueue_job_status_email`).

**Training engine files modified:**
- `training_engine/utils/notify.py` — `enqueue_job_status_slack()` +
  `enqueue_job_status_notifications()` (email + Slack fan-out via `send_task` by name).
- `training_engine/utils/job_status.py` — calls unified
  `enqueue_job_status_notifications` from `mark_job_completed`/`mark_job_failed`.

**Config:**
- `SLACK_WEBHOOK_URL` already in Settings + `.env.example` (no change needed).

**Trigger points (unchanged from PHASE4-003, now fan out to both channels):**
1. Training completes or fails in GPU worker → `job_status.mark_job_*` → notify enqueue.
2. Backend dispatch rejects job (rlhf / no dataset) → `training_tasks._mark_job_failed`
   → notify enqueue.

**Verification:**
- `uv run pytest` — backend notification tests 38/38, training_engine notify+job_status 22/22.
- `uv run ruff check` — clean on all touched files.
- No live Slack webhook tested (URL unset in dev — expected no-op path).

## GOTCHAS LOGGED
- Slack fires only on `completed`/`failed`, same as email — not `queued`/`running`/`pending`.
- Webhook is optional; dev works without `SLACK_WEBHOOK_URL` (logs `slack_skipped_webhook_not_configured`).
- Fan-out is two separate Celery tasks (email + Slack), not one combined task — keeps channels
  independently retryable and optional.
- `training_engine/utils/notify.py` still cannot import apps/backend — uses `send_task` by name.
- Slack Block Kit button links to `FRONTEND_URL/training/{job_id}` (same deep link as email).
