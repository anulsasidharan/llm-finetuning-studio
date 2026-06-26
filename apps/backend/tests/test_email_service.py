from unittest.mock import MagicMock, patch

from services.email_service import send_email, smtp_configured


def test_smtp_configured_false_when_credentials_missing(monkeypatch) -> None:
    monkeypatch.setattr("services.email_service.settings.SMTP_USER", "")
    monkeypatch.setattr("services.email_service.settings.SMTP_PASSWORD", "")
    assert smtp_configured() is False


def test_smtp_configured_true_when_credentials_present(monkeypatch) -> None:
    monkeypatch.setattr("services.email_service.settings.SMTP_USER", "user@example.com")
    monkeypatch.setattr("services.email_service.settings.SMTP_PASSWORD", "secret")
    assert smtp_configured() is True


def test_send_email_skips_when_smtp_not_configured(monkeypatch) -> None:
    monkeypatch.setattr("services.email_service.settings.SMTP_USER", "")
    monkeypatch.setattr("services.email_service.settings.SMTP_PASSWORD", "")
    with patch("services.email_service.smtplib.SMTP") as mock_smtp:
        send_email(to="user@example.com", subject="Test", body_text="Hello")
    mock_smtp.assert_not_called()


def test_send_email_uses_starttls_and_login(monkeypatch) -> None:
    monkeypatch.setattr("services.email_service.settings.SMTP_USER", "sender@example.com")
    monkeypatch.setattr("services.email_service.settings.SMTP_PASSWORD", "secret")
    monkeypatch.setattr("services.email_service.settings.SMTP_HOST", "smtp.example.com")
    monkeypatch.setattr("services.email_service.settings.SMTP_PORT", 587)
    monkeypatch.setattr(
        "services.email_service.settings.NOTIFICATION_FROM_EMAIL", "noreply@example.com"
    )

    smtp_instance = MagicMock()
    smtp_instance.__enter__.return_value = smtp_instance
    smtp_instance.__exit__.return_value = False
    with patch("services.email_service.smtplib.SMTP", return_value=smtp_instance) as mock_smtp:
        send_email(
            to="user@example.com",
            subject="Job done",
            body_text="Plain body",
            body_html="<p>HTML body</p>",
        )

    mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=30)
    smtp_instance.starttls.assert_called_once()
    smtp_instance.login.assert_called_once_with("sender@example.com", "secret")
    smtp_instance.send_message.assert_called_once()
