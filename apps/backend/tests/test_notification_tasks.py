from unittest.mock import patch

from tasks.notification_tasks import send_job_status_email, send_job_status_slack


def test_send_job_status_email_delegates_to_service() -> None:
    with patch("tasks.notification_tasks.deliver_job_status_email") as mock_deliver:
        send_job_status_email.run(job_id="job-1", status="completed")
    mock_deliver.assert_called_once_with(job_id="job-1", status="completed", error=None)


def test_send_job_status_email_swallows_service_errors() -> None:
    with patch(
        "tasks.notification_tasks.deliver_job_status_email",
        side_effect=RuntimeError("smtp down"),
    ):
        send_job_status_email.run(job_id="job-1", status="failed", error="boom")


def test_send_job_status_slack_delegates_to_service() -> None:
    with patch("tasks.notification_tasks.deliver_job_status_slack") as mock_deliver:
        send_job_status_slack.run(job_id="job-1", status="completed")
    mock_deliver.assert_called_once_with(job_id="job-1", status="completed", error=None)


def test_send_job_status_slack_swallows_service_errors() -> None:
    with patch(
        "tasks.notification_tasks.deliver_job_status_slack",
        side_effect=RuntimeError("slack down"),
    ):
        send_job_status_slack.run(job_id="job-1", status="failed", error="boom")
