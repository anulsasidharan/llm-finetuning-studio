from typing import Any
from unittest.mock import MagicMock, patch

from utils.job_status import (
    MetricsPersistCallback,
    _database_url,
    mark_job_completed,
    mark_job_failed,
    mark_job_running,
    update_job_metrics,
)


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


def _patched_connect() -> tuple[_FakeConn, Any]:
    fake_conn = _FakeConn()
    patcher = patch("utils.job_status._connect", return_value=fake_conn)
    return fake_conn, patcher


def test_database_url_falls_back_when_env_unset(monkeypatch: Any) -> None:
    monkeypatch.delenv("DATABASE_URL_SYNC", raising=False)
    assert _database_url() == (
        "postgresql://fts_user:fts_password_change_in_production@localhost:5433/fts_db"
    )


def test_database_url_reads_env_var(monkeypatch: Any) -> None:
    monkeypatch.setenv("DATABASE_URL_SYNC", "postgresql://u:p@host:5432/db")
    assert _database_url() == "postgresql://u:p@host:5432/db"


def test_mark_job_running_updates_status() -> None:
    fake_conn, patcher = _patched_connect()
    with patcher:
        mark_job_running("job-1")

    query, params = fake_conn.cursor_obj.calls[0]
    assert "status" in query
    assert params == {"status": "running", "job_id": "job-1"}
    assert fake_conn.closed is True


def test_mark_job_completed_writes_status_and_losses() -> None:
    fake_conn, patcher = _patched_connect()
    with patcher:
        mark_job_completed("job-1", train_loss=0.5, eval_loss=0.4)

    _, params = fake_conn.cursor_obj.calls[0]
    assert params == {
        "status": "completed",
        "train_loss": 0.5,
        "eval_loss": 0.4,
        "job_id": "job-1",
    }


def test_mark_job_failed_writes_failed_status() -> None:
    fake_conn, patcher = _patched_connect()
    with patcher:
        mark_job_failed("job-1", "boom")

    _, params = fake_conn.cursor_obj.calls[0]
    assert params == {"status": "failed", "job_id": "job-1"}


def test_mark_job_failed_swallows_db_errors() -> None:
    with patch("utils.job_status._connect", side_effect=RuntimeError("no db")):
        mark_job_failed("job-1", "boom")  # must not raise


def test_update_job_metrics_writes_all_fields() -> None:
    fake_conn, patcher = _patched_connect()
    with patcher:
        update_job_metrics(
            "job-1",
            train_loss=0.5,
            eval_loss=0.4,
            gpu_utilization_pct=55.0,
            vram_used_gb=8.0,
            tokens_per_second=12.5,
        )

    _, params = fake_conn.cursor_obj.calls[0]
    assert params == {
        "train_loss": 0.5,
        "eval_loss": 0.4,
        "gpu_utilization_pct": 55.0,
        "vram_used_gb": 8.0,
        "tokens_per_second": 12.5,
        "job_id": "job-1",
    }


def test_update_job_metrics_swallows_db_errors() -> None:
    with patch("utils.job_status._connect", side_effect=RuntimeError("no db")):
        update_job_metrics("job-1", train_loss=0.5)  # must not raise


def _state(global_step: int = 5, epoch: float = 1.0) -> MagicMock:
    state = MagicMock()
    state.global_step = global_step
    state.epoch = epoch
    return state


def test_metrics_persist_callback_on_log_writes_train_loss() -> None:
    with patch("utils.job_status.update_job_metrics") as mock_update:
        callback = MetricsPersistCallback(job_id="job-1")
        callback.on_log(
            args=MagicMock(),
            state=_state(),
            control=MagicMock(),
            logs={"loss": 0.5, "epoch": 1.0},
        )

    mock_update.assert_called_once_with(
        "job-1",
        train_loss=0.5,
        eval_loss=None,
        gpu_utilization_pct=None,
        vram_used_gb=None,
        tokens_per_second=None,
    )


def test_metrics_persist_callback_on_log_skips_when_no_loss_present() -> None:
    with patch("utils.job_status.update_job_metrics") as mock_update:
        callback = MetricsPersistCallback(job_id="job-1")
        callback.on_log(args=MagicMock(), state=_state(), control=MagicMock(), logs={})

    mock_update.assert_not_called()


def test_metrics_persist_callback_includes_gpu_stats_from_monitor() -> None:
    gpu_monitor = MagicMock(return_value={"gpu_utilization_pct": 42.0, "vram_used_gb": 6.0})
    with patch("utils.job_status.update_job_metrics") as mock_update:
        callback = MetricsPersistCallback(job_id="job-1", gpu_monitor=gpu_monitor)
        callback.on_log(
            args=MagicMock(),
            state=_state(),
            control=MagicMock(),
            logs={"loss": 0.5},
        )

    mock_update.assert_called_once_with(
        "job-1",
        train_loss=0.5,
        eval_loss=None,
        gpu_utilization_pct=42.0,
        vram_used_gb=6.0,
        tokens_per_second=None,
    )


def test_metrics_persist_callback_on_evaluate_writes_eval_loss() -> None:
    with patch("utils.job_status.update_job_metrics") as mock_update:
        callback = MetricsPersistCallback(job_id="job-1")
        callback.on_evaluate(
            args=MagicMock(), state=_state(), control=MagicMock(), metrics={"eval_loss": 0.3}
        )

    mock_update.assert_called_once_with("job-1", eval_loss=0.3)


def test_metrics_persist_callback_on_evaluate_skips_without_eval_loss() -> None:
    with patch("utils.job_status.update_job_metrics") as mock_update:
        callback = MetricsPersistCallback(job_id="job-1")
        callback.on_evaluate(args=MagicMock(), state=_state(), control=MagicMock(), metrics={})

    mock_update.assert_not_called()
