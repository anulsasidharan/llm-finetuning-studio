"""GPUMonitor — pynvml-based live GPU utilization/VRAM sampling.

Returns exactly the two keys ``utils.callbacks.MetricsCallback._gpu_stats()``
already merges into its payload (``gpu_utilization_pct``, ``vram_used_gb``),
so ``GPUMonitor(...).sample`` can be passed straight into
``MetricsCallback(gpu_monitor=...)`` with no adapter glue.
"""

from __future__ import annotations

from typing import Any

import structlog

logger = structlog.get_logger()

_BYTES_PER_GB = 1024**3


def _get_pynvml() -> Any:
    import pynvml

    return pynvml


class GPUMonitor:
    """Samples live utilization/VRAM for a single NVIDIA GPU via ``pynvml``.

    No GPU is guaranteed to be present in dev/CI — ``pynvml.nvmlInit()``
    raises (e.g. ``NVMLError_LibraryNotFound``) on a machine with no NVIDIA
    driver. ``sample()`` degrades gracefully (returns ``{}``) on any failure
    rather than raising, since it is called from inside ``MetricsCallback``
    on every ``on_log``/``on_evaluate`` hook of a real, expensive, long-
    running training run.

    ``pynvml`` is imported lazily via ``_get_pynvml()`` (mirrors the
    lazy-import pattern used for ``BitsAndBytesConfig``/``trl`` elsewhere in
    ``training_engine``) so unit tests can mock it out entirely — never call
    real NVML in CI/unit tests.
    """

    def __init__(self, device_index: int = 0) -> None:
        self.device_index = device_index

    def sample(self) -> dict[str, float]:
        try:
            pynvml = _get_pynvml()
            pynvml.nvmlInit()
        except Exception as exc:
            logger.warning(
                "gpu_monitor_nvml_init_failed",
                device_index=self.device_index,
                error=str(exc),
            )
            return {}

        try:
            handle = pynvml.nvmlDeviceGetHandleByIndex(self.device_index)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            return {
                "gpu_utilization_pct": float(utilization.gpu),
                "vram_used_gb": memory.used / _BYTES_PER_GB,
            }
        except Exception as exc:
            logger.warning(
                "gpu_monitor_sample_failed",
                device_index=self.device_index,
                error=str(exc),
            )
            return {}
        finally:
            try:
                pynvml.nvmlShutdown()
            except Exception as exc:
                logger.warning(
                    "gpu_monitor_nvml_shutdown_failed",
                    device_index=self.device_index,
                    error=str(exc),
                )

    def __call__(self) -> dict[str, float]:
        return self.sample()
