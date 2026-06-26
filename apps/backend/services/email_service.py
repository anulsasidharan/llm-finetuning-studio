"""SMTP email delivery — optional when SMTP_USER/SMTP_PASSWORD are unset."""

from __future__ import annotations

import smtplib
from email.message import EmailMessage

import structlog
from core.config import settings

logger = structlog.get_logger()


def smtp_configured() -> bool:
    return bool(settings.SMTP_USER and settings.SMTP_PASSWORD)


def send_email(
    *,
    to: str,
    subject: str,
    body_text: str,
    body_html: str | None = None,
) -> None:
    if not smtp_configured():
        logger.info("email_skipped_smtp_not_configured", to=to, subject=subject)
        return

    message = EmailMessage()
    message["From"] = settings.NOTIFICATION_FROM_EMAIL
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body_text)
    if body_html is not None:
        message.add_alternative(body_html, subtype="html")

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as smtp:
        smtp.starttls()
        smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        smtp.send_message(message)

    logger.info("email_sent", to=to, subject=subject)
