from unittest.mock import patch

from services.notification_service import (
    JobNotificationContext,
    _build_body_text,
    _build_subject,
    deliver_job_status_email,
)


def _sample_context(
    *, status: str = "completed", error: str | None = None
) -> JobNotificationContext:
    return JobNotificationContext(
        job_id="job-1",
        status=status,
        base_model_id="meta-llama/Meta-Llama-3-8B",
        methodology="qlora",
        user_email="user@example.com",
        user_name="Test User",
        train_loss=0.42,
        eval_loss=0.38,
        error=error,
    )


def test_build_subject_completed() -> None:
    assert "completed" in _build_subject(_sample_context()).lower()


def test_build_subject_failed() -> None:
    assert "failed" in _build_subject(_sample_context(status="failed")).lower()


def test_build_body_text_includes_dashboard_link(monkeypatch) -> None:
    monkeypatch.setattr(
        "services.notification_service.settings.FRONTEND_URL", "http://localhost:3000"
    )
    body = _build_body_text(_sample_context())
    assert "http://localhost:3000/training/job-1" in body
    assert "QLORA" in body
    assert "0.4200" in body


def test_build_body_text_failed_includes_error() -> None:
    body = _build_body_text(_sample_context(status="failed", error="CUDA OOM"))
    assert "CUDA OOM" in body


def test_deliver_job_status_email_skips_non_terminal_status() -> None:
    with patch("services.notification_service.send_email") as mock_send:
        deliver_job_status_email(job_id="job-1", status="running")
    mock_send.assert_not_called()


def test_deliver_job_status_email_sends_when_context_found() -> None:
    ctx = _sample_context()
    with (
        patch(
            "services.notification_service._fetch_job_context",
            return_value=ctx,
        ),
        patch("services.notification_service.send_email") as mock_send,
    ):
        deliver_job_status_email(job_id="job-1", status="completed")

    mock_send.assert_called_once()
    kwargs = mock_send.call_args.kwargs
    assert kwargs["to"] == "user@example.com"
    assert "completed" in kwargs["subject"].lower()
    assert "job-1" in kwargs["body_text"]


def test_deliver_job_status_email_noop_when_job_missing() -> None:
    with (
        patch("services.notification_service._fetch_job_context", return_value=None),
        patch("services.notification_service.send_email") as mock_send,
    ):
        deliver_job_status_email(job_id="missing", status="failed", error="boom")
    mock_send.assert_not_called()
