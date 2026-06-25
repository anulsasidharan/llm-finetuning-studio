from typing import Any
from unittest.mock import patch

from tasks.eval_tasks import dispatch_eval_job


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
    eval_id="eval-1",
    eval_type="compare",
    base_model_id="gpt2",
    finetuned_model_id="gpt2-ft",
    prompts=["hello"],
    benchmarks=None,
    max_new_tokens=256,
    num_fewshot=None,
    sample_limit=None,
)


def _run(**overrides: Any) -> None:
    kwargs = {**VALID_KWARGS, **overrides}
    return dispatch_eval_job.run(**kwargs)


def test_dispatch_eval_job_marks_queued_and_sends_task() -> None:
    fake_conn = _FakeConn()
    with (
        patch("tasks.eval_tasks._connect", return_value=fake_conn),
        patch("tasks.eval_tasks.celery.send_task") as mock_send,
    ):
        _run()

    _, params = fake_conn.cursor_obj.calls[0]
    assert params == {"status": "queued", "eval_id": "eval-1"}

    mock_send.assert_called_once_with(
        "training_engine.tasks.run_eval_job",
        kwargs={
            "eval_id": "eval-1",
            "eval_type": "compare",
            "base_model_id": "gpt2",
            "finetuned_model_id": "gpt2-ft",
            "prompts": ["hello"],
            "benchmarks": None,
            "max_new_tokens": 256,
            "num_fewshot": None,
            "sample_limit": None,
        },
        queue="gpu_training",
    )


def test_dispatch_eval_job_closes_connection() -> None:
    fake_conn = _FakeConn()
    with (
        patch("tasks.eval_tasks._connect", return_value=fake_conn),
        patch("tasks.eval_tasks.celery.send_task"),
    ):
        _run()

    assert fake_conn.closed is True
