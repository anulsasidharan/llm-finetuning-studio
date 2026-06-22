from typing import Any
from unittest.mock import patch

from tasks.training_tasks import dispatch_training_job


class _FakeCursor:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, query: str, params: dict[str, Any]) -> None:
        self.calls.append((query, params))

    def __enter__(self) -> "_FakeCursor":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False


class _FakeConn:
    def __init__(self) -> None:
        self.cursor_obj = _FakeCursor()
        self.closed = False

    def cursor(self) -> _FakeCursor:
        return self.cursor_obj

    def __enter__(self) -> "_FakeConn":
        return self

    def __exit__(self, *exc_info: object) -> bool:
        return False

    def close(self) -> None:
        self.closed = True


VALID_KWARGS = dict(
    job_id="job-1",
    base_model_id="meta-llama/Meta-Llama-3-8B",
    methodology="sft",
    training_config={"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
    dataset_storage_path="user/file.jsonl",
    dataset_format="chatml",
)


def _run(**overrides: Any) -> None:
    kwargs = {**VALID_KWARGS, **overrides}
    return dispatch_training_job.run(**kwargs)


def test_dispatch_rejects_rlhf_methodology() -> None:
    fake_conn = _FakeConn()
    with (
        patch("tasks.training_tasks._connect", return_value=fake_conn),
        patch("tasks.training_tasks.celery.send_task") as mock_send,
    ):
        _run(methodology="rlhf")

    _, params = fake_conn.cursor_obj.calls[0]
    assert params == {"status": "failed", "job_id": "job-1"}
    mock_send.assert_not_called()


def test_dispatch_marks_failed_when_no_dataset_attached() -> None:
    fake_conn = _FakeConn()
    with (
        patch("tasks.training_tasks._connect", return_value=fake_conn),
        patch("tasks.training_tasks.celery.send_task") as mock_send,
    ):
        _run(dataset_storage_path=None)

    _, params = fake_conn.cursor_obj.calls[0]
    assert params == {"status": "failed", "job_id": "job-1"}
    mock_send.assert_not_called()


def test_dispatch_happy_path_marks_queued_and_sends_task() -> None:
    fake_conn = _FakeConn()
    with (
        patch("tasks.training_tasks._connect", return_value=fake_conn),
        patch("tasks.training_tasks.celery.send_task") as mock_send,
    ):
        _run()

    _, params = fake_conn.cursor_obj.calls[0]
    assert params == {"status": "queued", "job_id": "job-1"}

    mock_send.assert_called_once_with(
        "training_engine.tasks.run_training_job",
        kwargs={
            "job_id": "job-1",
            "base_model_id": "meta-llama/Meta-Llama-3-8B",
            "methodology": "sft",
            "training_config": VALID_KWARGS["training_config"],
            "dataset_storage_path": "user/file.jsonl",
            "dataset_format": "chatml",
        },
        queue="gpu_training",
    )


def test_dispatch_defaults_dataset_format_to_unknown() -> None:
    fake_conn = _FakeConn()
    with (
        patch("tasks.training_tasks._connect", return_value=fake_conn),
        patch("tasks.training_tasks.celery.send_task") as mock_send,
    ):
        _run(dataset_format=None)

    sent_kwargs = mock_send.call_args.kwargs["kwargs"]
    assert sent_kwargs["dataset_format"] == "unknown"


def test_dispatch_closes_connection_even_when_send_task_not_reached() -> None:
    fake_conn = _FakeConn()
    with patch("tasks.training_tasks._connect", return_value=fake_conn):
        _run(methodology="rlhf")

    assert fake_conn.closed is True


def test_dispatch_publishes_status_change_on_queued() -> None:
    fake_conn = _FakeConn()
    with (
        patch("tasks.training_tasks._connect", return_value=fake_conn),
        patch("tasks.training_tasks.celery.send_task"),
        patch("tasks.training_tasks._publish_status_change") as mock_publish,
    ):
        _run()

    mock_publish.assert_called_once_with("job-1", "queued")


def test_dispatch_publishes_status_change_on_failure() -> None:
    fake_conn = _FakeConn()
    with (
        patch("tasks.training_tasks._connect", return_value=fake_conn),
        patch("tasks.training_tasks._publish_status_change") as mock_publish,
    ):
        _run(methodology="rlhf")

    mock_publish.assert_called_once_with("job-1", "failed")


def test_publish_status_change_swallows_redis_errors() -> None:
    from tasks.training_tasks import _publish_status_change

    with patch("tasks.training_tasks.redis.Redis.from_url", side_effect=ConnectionError("down")):
        _publish_status_change("job-1", "queued")  # must not raise
