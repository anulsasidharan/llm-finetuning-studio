from unittest.mock import MagicMock, patch

from utils.notify import (
    enqueue_job_status_email,
    enqueue_job_status_notifications,
    enqueue_job_status_slack,
)


def test_enqueue_job_status_email_sends_default_queue_task() -> None:
    mock_client = MagicMock()
    with (
        patch("celery.Celery", return_value=mock_client) as mock_celery_ctor,
        patch.dict("os.environ", {"CELERY_BROKER_URL": "redis://broker:6379/1"}, clear=False),
    ):
        enqueue_job_status_email(job_id="job-1", status="completed")

    mock_celery_ctor.assert_called_once_with(broker="redis://broker:6379/1")
    mock_client.send_task.assert_called_once_with(
        "tasks.notification_tasks.send_job_status_email",
        kwargs={"job_id": "job-1", "status": "completed", "error": None},
        queue="default",
    )


def test_enqueue_job_status_slack_sends_default_queue_task() -> None:
    mock_client = MagicMock()
    with (
        patch("celery.Celery", return_value=mock_client) as mock_celery_ctor,
        patch.dict("os.environ", {"CELERY_BROKER_URL": "redis://broker:6379/1"}, clear=False),
    ):
        enqueue_job_status_slack(job_id="job-1", status="failed", error="boom")

    mock_celery_ctor.assert_called_once_with(broker="redis://broker:6379/1")
    mock_client.send_task.assert_called_once_with(
        "tasks.notification_tasks.send_job_status_slack",
        kwargs={"job_id": "job-1", "status": "failed", "error": "boom"},
        queue="default",
    )


def test_enqueue_job_status_notifications_fans_out_email_and_slack() -> None:
    with (
        patch("utils.notify.enqueue_job_status_email") as mock_email,
        patch("utils.notify.enqueue_job_status_slack") as mock_slack,
    ):
        enqueue_job_status_notifications(job_id="job-1", status="completed")

    mock_email.assert_called_once_with(job_id="job-1", status="completed", error=None)
    mock_slack.assert_called_once_with(job_id="job-1", status="completed", error=None)


def test_enqueue_job_status_email_skips_non_terminal_status() -> None:
    with patch("celery.Celery") as mock_celery_ctor:
        enqueue_job_status_email(job_id="job-1", status="running")
    mock_celery_ctor.assert_not_called()


def test_enqueue_job_status_email_swallows_broker_errors() -> None:
    with patch("celery.Celery", side_effect=ConnectionError("down")):
        enqueue_job_status_email(job_id="job-1", status="failed", error="boom")
