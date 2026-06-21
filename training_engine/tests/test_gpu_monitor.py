import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from utils.callbacks import MetricsCallback
from utils.gpu_monitor import GPUMonitor


def _fake_pynvml(*, gpu_pct: float = 42.0, used_bytes: int = 4 * 1024**3) -> MagicMock:
    fake = MagicMock()
    fake.nvmlDeviceGetHandleByIndex.return_value = "handle-0"
    fake.nvmlDeviceGetUtilizationRates.return_value = SimpleNamespace(gpu=gpu_pct)
    fake.nvmlDeviceGetMemoryInfo.return_value = SimpleNamespace(used=used_bytes)
    return fake


def test_sample_returns_utilization_and_vram_on_success() -> None:
    fake = _fake_pynvml(gpu_pct=55.0, used_bytes=8 * 1024**3)
    with patch("utils.gpu_monitor._get_pynvml", return_value=fake):
        result = GPUMonitor().sample()

    assert result == {"gpu_utilization_pct": 55.0, "vram_used_gb": 8.0}
    fake.nvmlInit.assert_called_once()
    fake.nvmlShutdown.assert_called_once()


def test_sample_passes_device_index_to_handle_lookup() -> None:
    fake = _fake_pynvml()
    with patch("utils.gpu_monitor._get_pynvml", return_value=fake):
        GPUMonitor(device_index=2).sample()

    fake.nvmlDeviceGetHandleByIndex.assert_called_once_with(2)


def test_sample_returns_empty_dict_when_nvml_init_fails() -> None:
    fake = MagicMock()
    fake.nvmlInit.side_effect = RuntimeError("NVMLError_LibraryNotFound")
    with patch("utils.gpu_monitor._get_pynvml", return_value=fake):
        result = GPUMonitor().sample()

    assert result == {}
    fake.nvmlShutdown.assert_not_called()


def test_sample_returns_empty_dict_when_handle_lookup_fails() -> None:
    fake = MagicMock()
    fake.nvmlDeviceGetHandleByIndex.side_effect = RuntimeError("NVMLError_InvalidArgument")
    with patch("utils.gpu_monitor._get_pynvml", return_value=fake):
        result = GPUMonitor().sample()

    assert result == {}


def test_sample_shuts_down_nvml_even_when_sampling_fails() -> None:
    fake = MagicMock()
    fake.nvmlDeviceGetHandleByIndex.side_effect = RuntimeError("boom")
    with patch("utils.gpu_monitor._get_pynvml", return_value=fake):
        GPUMonitor().sample()

    fake.nvmlShutdown.assert_called_once()


def test_sample_swallows_shutdown_failure() -> None:
    fake = _fake_pynvml()
    fake.nvmlShutdown.side_effect = RuntimeError("shutdown boom")
    with patch("utils.gpu_monitor._get_pynvml", return_value=fake):
        result = GPUMonitor().sample()

    assert result == {"gpu_utilization_pct": 42.0, "vram_used_gb": 4.0}


def test_call_dunder_delegates_to_sample() -> None:
    fake = _fake_pynvml(gpu_pct=10.0, used_bytes=2 * 1024**3)
    with patch("utils.gpu_monitor._get_pynvml", return_value=fake):
        monitor = GPUMonitor()
        result = monitor()

    assert result == {"gpu_utilization_pct": 10.0, "vram_used_gb": 2.0}


def test_default_device_index_is_zero() -> None:
    assert GPUMonitor().device_index == 0


def test_wires_into_metrics_callback_gpu_monitor_kwarg() -> None:
    """GPUMonitor(...).sample is a clean drop-in for MetricsCallback(gpu_monitor=...).

    PHASE2-007 left ``gpu_monitor`` as an optional callable kwarg specifically
    so this PHASE2-008 monitor could be passed in with no adapter glue. The
    real Celery training task (PHASE2-009) constructs both this way.
    """
    fake = _fake_pynvml(gpu_pct=63.0, used_bytes=6 * 1024**3)
    mock_redis_client = MagicMock()
    with patch("utils.gpu_monitor._get_pynvml", return_value=fake):
        callback = MetricsCallback(
            job_id="job-456",
            redis_client=mock_redis_client,
            gpu_monitor=GPUMonitor(device_index=0).sample,
        )
        callback.on_log(
            args=MagicMock(),
            state=SimpleNamespace(global_step=1, epoch=0.1),
            control=MagicMock(),
            logs={"loss": 0.8},
        )

    _, raw_payload = mock_redis_client.publish.call_args[0]
    payload = json.loads(raw_payload)
    assert payload["gpu_utilization_pct"] == 63.0
    assert payload["vram_used_gb"] == 6.0
