"""Job status email notifications — fetches job + user context, composes and sends."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import structlog
from core.config import settings

from services.email_service import send_email
from services.slack_service import post_slack_message

logger = structlog.get_logger()

TERMINAL_STATUSES = frozenset({"completed", "failed"})


@dataclass(frozen=True)
class JobNotificationContext:
    job_id: str
    status: str
    base_model_id: str
    methodology: str
    user_email: str
    user_name: str
    train_loss: float | None = None
    eval_loss: float | None = None
    error: str | None = None


def _connect() -> Any:
    import psycopg2

    return psycopg2.connect(settings.DATABASE_URL_SYNC)


def _fetch_job_context(
    job_id: str, status: str, error: str | None
) -> JobNotificationContext | None:
    conn = _connect()
    try:
        with conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    j.id::text,
                    j.status,
                    j.base_model_id,
                    j.methodology,
                    j.train_loss,
                    j.eval_loss,
                    u.email,
                    u.full_name
                FROM fine_tune_jobs j
                JOIN users u ON u.id = j.user_id
                WHERE j.id = %(job_id)s
                """,
                {"job_id": job_id},
            )
            row = cur.fetchone()
    finally:
        conn.close()

    if row is None:
        logger.warning("job_notification_job_not_found", job_id=job_id)
        return None

    return JobNotificationContext(
        job_id=row[0],
        status=status,
        base_model_id=row[2],
        methodology=row[3],
        train_loss=row[4],
        eval_loss=row[5],
        user_email=row[6],
        user_name=row[7],
        error=error,
    )


def _training_dashboard_url(job_id: str) -> str:
    base = settings.FRONTEND_URL.rstrip("/")
    return f"{base}/training/{job_id}"


def _format_loss(value: float | None) -> str:
    return f"{value:.4f}" if value is not None else "—"


def _build_subject(ctx: JobNotificationContext) -> str:
    if ctx.status == "completed":
        return f"[{settings.APP_NAME}] Training job completed"
    return f"[{settings.APP_NAME}] Training job failed"


def _build_body_text(ctx: JobNotificationContext) -> str:
    lines = [
        f"Hi {ctx.user_name},",
        "",
    ]
    if ctx.status == "completed":
        lines.append("Your fine-tuning job has completed successfully.")
    else:
        lines.append("Your fine-tuning job has failed.")

    lines.extend(
        [
            "",
            f"Job ID:       {ctx.job_id}",
            f"Base model:   {ctx.base_model_id}",
            f"Methodology:  {ctx.methodology.upper()}",
            f"Status:       {ctx.status}",
        ]
    )

    if ctx.status == "completed":
        lines.extend(
            [
                f"Train loss:   {_format_loss(ctx.train_loss)}",
                f"Eval loss:    {_format_loss(ctx.eval_loss)}",
            ]
        )
    elif ctx.error:
        lines.extend(["", f"Error: {ctx.error}"])

    lines.extend(
        [
            "",
            f"View details: {_training_dashboard_url(ctx.job_id)}",
            "",
            f"— {settings.APP_NAME}",
        ]
    )
    return "\n".join(lines)


def _build_body_html(ctx: JobNotificationContext) -> str:
    dashboard_url = _training_dashboard_url(ctx.job_id)
    intro = (
        "Your fine-tuning job has completed successfully."
        if ctx.status == "completed"
        else "Your fine-tuning job has failed."
    )
    error_block = ""
    if ctx.status == "failed" and ctx.error:
        error_block = f"<p><strong>Error:</strong> {ctx.error}</p>"

    metrics_block = ""
    if ctx.status == "completed":
        metrics_block = (
            f"<p>Train loss: {_format_loss(ctx.train_loss)}<br>"
            f"Eval loss: {_format_loss(ctx.eval_loss)}</p>"
        )

    return f"""\
<!DOCTYPE html>
<html>
<body style="font-family: sans-serif; line-height: 1.5; color: #111;">
  <p>Hi {ctx.user_name},</p>
  <p>{intro}</p>
  <table style="border-collapse: collapse;">
    <tr><td style="padding-right: 12px;"><strong>Job ID</strong></td><td>{ctx.job_id}</td></tr>
    <tr><td style="padding-right: 12px;"><strong>Base model</strong></td><td>{ctx.base_model_id}</td></tr>
    <tr><td style="padding-right: 12px;"><strong>Methodology</strong></td><td>{ctx.methodology.upper()}</td></tr>
    <tr><td style="padding-right: 12px;"><strong>Status</strong></td><td>{ctx.status}</td></tr>
  </table>
  {metrics_block}
  {error_block}
  <p><a href="{dashboard_url}">View training dashboard</a></p>
  <p style="color: #666;">— {settings.APP_NAME}</p>
</body>
</html>"""


def _build_slack_text(ctx: JobNotificationContext) -> str:
    headline = (
        "Training job completed successfully"
        if ctx.status == "completed"
        else "Training job failed"
    )
    return (
        f"{headline}: {ctx.base_model_id} ({ctx.methodology.upper()}) — "
        f"job {ctx.job_id} for {ctx.user_name}"
    )


def _build_slack_blocks(ctx: JobNotificationContext) -> list[dict[str, object]]:
    dashboard_url = _training_dashboard_url(ctx.job_id)
    headline = (
        f":white_check_mark: {settings.APP_NAME} — training job completed"
        if ctx.status == "completed"
        else f":x: {settings.APP_NAME} — training job failed"
    )
    fields: list[dict[str, object]] = [
        {"type": "mrkdwn", "text": f"*Job ID*\n`{ctx.job_id}`"},
        {"type": "mrkdwn", "text": f"*User*\n{ctx.user_name} ({ctx.user_email})"},
        {"type": "mrkdwn", "text": f"*Base model*\n{ctx.base_model_id}"},
        {"type": "mrkdwn", "text": f"*Methodology*\n{ctx.methodology.upper()}"},
    ]
    if ctx.status == "completed":
        fields.extend(
            [
                {"type": "mrkdwn", "text": f"*Train loss*\n{_format_loss(ctx.train_loss)}"},
                {"type": "mrkdwn", "text": f"*Eval loss*\n{_format_loss(ctx.eval_loss)}"},
            ]
        )
    elif ctx.error:
        fields.append({"type": "mrkdwn", "text": f"*Error*\n{ctx.error}"})

    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": headline, "emoji": True},
        },
        {"type": "section", "fields": fields},
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "View training dashboard"},
                    "url": dashboard_url,
                }
            ],
        },
    ]


def deliver_job_status_email(*, job_id: str, status: str, error: str | None = None) -> None:
    if status not in TERMINAL_STATUSES:
        logger.info("job_notification_skipped_non_terminal", job_id=job_id, status=status)
        return

    ctx = _fetch_job_context(job_id, status, error)
    if ctx is None:
        return

    send_email(
        to=ctx.user_email,
        subject=_build_subject(ctx),
        body_text=_build_body_text(ctx),
        body_html=_build_body_html(ctx),
    )


def deliver_job_status_slack(*, job_id: str, status: str, error: str | None = None) -> None:
    if status not in TERMINAL_STATUSES:
        logger.info("job_notification_skipped_non_terminal", job_id=job_id, status=status)
        return

    ctx = _fetch_job_context(job_id, status, error)
    if ctx is None:
        return

    post_slack_message(
        text=_build_slack_text(ctx),
        blocks=_build_slack_blocks(ctx),
    )
