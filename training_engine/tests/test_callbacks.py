import json
from typing import Any
from unittest.mock import MagicMock, patch

from utils.callbacks import MetricsCallback, _default_redis_url, publish_status_change


def _state(global_step: int = 5, epoch: float = 1.0) -> MagicMock:
    state = MagicMock()
    state.global_step = global_step
    state.epoch = epoch
    return state


def _make_callback(**kwargs: Any) -> tuple[MetricsCallback, MagicMock]:
    mock_client = MagicMock()
    defaults: dict[str, Any] = {"job_id": "job-123", "redis_client": mock_client}
    defaults.update(kwargs)
    return MetricsCallback(**defaults), mock_client


def test_channel_name_follows_documented_convention() -> None:
    callback, _ = _make_callback()
    assert callback.channel == "training_metrics:job-123"


def test_custom_channel_overrides_default() -> None:
    callback, _ = _make_callback(channel="custom:channel")
    assert callback.channel == "custom:channel"


def test_default_redis_url_falls_back_when_env_unset(monkeypatch: Any) -> None:
    monkeypatch.delenv("TRAINING_ENGINE_REDIS_URL", raising=False)
    assert _default_redis_url() == "redis://localhost:6380/3"


def test_default_redis_url_reads_env_var(monkeypatch: Any) -> None:
    monkeypatch.setenv("TRAINING_ENGINE_REDIS_URL", "redis://:pw@redis:6379/3")
    assert _default_redis_url() == "redis://:pw@redis:6379/3"


def test_on_log_publishes_train_loss() -> None:
    callback, mock_client = _make_callback()
    callback.on_log(
        args=MagicMock(),
        state=_state(global_step=10),
        control=MagicMock(),
        logs={"loss": 0.5, "epoch": 1.0},
    )

    mock_client.publish.assert_called_once()
    channel, raw_payload = mock_client.publish.call_args[0]
    payload = json.loads(raw_payload)
    assert channel == "training_metrics:job-123"
    assert payload["type"] == "metrics_update"
    assert payload["job_id"] == "job-123"
    assert payload["step"] == 10
    assert payload["epoch"] == 1.0
    assert payload["train_loss"] == 0.5
    assert payload["eval_loss"] is None


def test_on_log_ignores_logs_without_loss_or_eval_loss() -> None:
    callback, mock_client = _make_callback()
    callback.on_log(
        args=MagicMock(), state=_state(), control=MagicMock(), logs={"learning_rate": 1e-4}
    )

    mock_client.publish.assert_not_called()


def test_on_log_ignores_empty_logs() -> None:
    callback, mock_client = _make_callback()
    callback.on_log(args=MagicMock(), state=_state(), control=MagicMock(), logs=None)
    callback.on_log(args=MagicMock(), state=_state(), control=MagicMock(), logs={})

    mock_client.publish.assert_not_called()


def test_on_evaluate_publishes_eval_loss() -> None:
    callback, mock_client = _make_callback()
    callback.on_evaluate(
        args=MagicMock(),
        state=_state(global_step=20, epoch=2.0),
        control=MagicMock(),
        metrics={"eval_loss": 0.2},
    )

    mock_client.publish.assert_called_once()
    _, raw_payload = mock_client.publish.call_args[0]
    payload = json.loads(raw_payload)
    assert payload["step"] == 20
    assert payload["epoch"] == 2.0
    assert payload["eval_loss"] == 0.2
    assert payload["train_loss"] is None


def test_on_evaluate_ignores_metrics_without_eval_loss() -> None:
    callback, mock_client = _make_callback()
    callback.on_evaluate(
        args=MagicMock(), state=_state(), control=MagicMock(), metrics={"eval_runtime": 1.2}
    )

    mock_client.publish.assert_not_called()


def test_gpu_monitor_stats_included_when_provided() -> None:
    gpu_monitor = MagicMock(return_value={"gpu_utilization_pct": 87.5, "vram_used_gb": 12.3})
    callback, mock_client = _make_callback(gpu_monitor=gpu_monitor)
    callback.on_log(args=MagicMock(), state=_state(), control=MagicMock(), logs={"loss": 0.1})

    gpu_monitor.assert_called_once()
    _, raw_payload = mock_client.publish.call_args[0]
    payload = json.loads(raw_payload)
    assert payload["gpu_utilization_pct"] == 87.5
    assert payload["vram_used_gb"] == 12.3


def test_gpu_fields_are_none_without_gpu_monitor() -> None:
    callback, mock_client = _make_callback()
    callback.on_log(args=MagicMock(), state=_state(), control=MagicMock(), logs={"loss": 0.1})

    _, raw_payload = mock_client.publish.call_args[0]
    payload = json.loads(raw_payload)
    assert payload["gpu_utilization_pct"] is None
    assert payload["vram_used_gb"] is None


def test_publish_failure_is_swallowed_not_raised() -> None:
    callback, mock_client = _make_callback()
    mock_client.publish.side_effect = ConnectionError("redis unreachable")

    callback.on_log(args=MagicMock(), state=_state(), control=MagicMock(), logs={"loss": 0.1})


@patch("utils.callbacks.redis")
def test_lazy_redis_client_built_from_url_when_not_injected(mock_redis_module: MagicMock) -> None:
    mock_redis_module.Redis.from_url.return_value = MagicMock()
    callback = MetricsCallback(job_id="job-456", redis_url="redis://localhost:6380/3")

    client = callback._get_redis_client()

    mock_redis_module.Redis.from_url.assert_called_once_with("redis://localhost:6380/3")
    assert client is mock_redis_module.Redis.from_url.return_value


def test_injected_redis_client_is_reused_without_building_one() -> None:
    callback, mock_client = _make_callback()
    assert callback._get_redis_client() is mock_client


def test_publish_status_change_publishes_to_default_channel() -> None:
    mock_client = MagicMock()

    publish_status_change(job_id="job-123", status="running", redis_client=mock_client)

    mock_client.publish.assert_called_once()
    channel, raw_payload = mock_client.publish.call_args[0]
    assert channel == "training_metrics:job-123"
    payload = json.loads(raw_payload)
    assert payload == {"type": "status_change", "job_id": "job-123", "status": "running"}


def test_publish_status_change_respects_custom_channel() -> None:
    mock_client = MagicMock()

    publish_status_change(
        job_id="job-123", status="completed", redis_client=mock_client, channel="custom:channel"
    )

    channel, _ = mock_client.publish.call_args[0]
    assert channel == "custom:channel"


def test_publish_status_change_failure_is_swallowed_not_raised() -> None:
    mock_client = MagicMock()
    mock_client.publish.side_effect = ConnectionError("redis unreachable")

    publish_status_change(job_id="job-123", status="failed", redis_client=mock_client)


@patch("utils.callbacks.redis")
def test_publish_status_change_builds_client_from_url_when_not_injected(
    mock_redis_module: MagicMock,
) -> None:
    mock_redis_module.Redis.from_url.return_value = MagicMock()

    publish_status_change(job_id="job-456", status="running", redis_url="redis://localhost:6380/3")

    mock_redis_module.Redis.from_url.assert_called_once_with("redis://localhost:6380/3")
