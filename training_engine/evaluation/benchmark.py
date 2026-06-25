"""Benchmark a model on standard academic suites (MMLU, HellaSwag, ARC) via lm-evaluation-harness."""

from __future__ import annotations

from typing import Any

import structlog
from transformers import PreTrainedModel, PreTrainedTokenizerBase
from utils.hf_datasets import ensure_hf_datasets_loaded

logger = structlog.get_logger()

BENCHMARK_TASKS: dict[str, tuple[str, ...]] = {
    "mmlu": ("mmlu",),
    "hellaswag": ("hellaswag",),
    "arc": ("arc_easy", "arc_challenge"),
}
SUPPORTED_BENCHMARKS: frozenset[str] = frozenset(BENCHMARK_TASKS)


class BenchmarkError(ValueError):
    """Raised when benchmark inputs or setup are invalid."""


def _get_lm_eval() -> Any:
    # lm_eval pulls in `evaluate` -> `datasets` at import time, which hits the
    # same local-package naming collision TRL does (see MEMORY.md) -- resolve
    # the real HuggingFace `datasets` first, exactly like the trainers do.
    ensure_hf_datasets_loaded()
    import lm_eval

    return lm_eval


def _get_hflm_cls() -> type:
    ensure_hf_datasets_loaded()
    from lm_eval.models.huggingface import HFLM

    return HFLM


def _resolve_device() -> str:
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _resolve_task_names(benchmarks: list[str]) -> list[str]:
    unknown = sorted(set(benchmarks) - SUPPORTED_BENCHMARKS)
    if unknown:
        raise BenchmarkError(
            f"Unsupported benchmark(s): {unknown}. Must be one of {sorted(SUPPORTED_BENCHMARKS)}."
        )

    task_names: list[str] = []
    for benchmark in benchmarks:
        task_names.extend(BENCHMARK_TASKS[benchmark])
    return task_names


def _extract_metrics(
    raw_results: dict[str, Any],
    benchmarks: list[str],
) -> dict[str, dict[str, Any]]:
    """Reshape lm-eval's flat per-task ``results`` dict into one entry per requested benchmark."""
    task_results = raw_results.get("results", {})
    metrics: dict[str, dict[str, Any]] = {}
    for benchmark in benchmarks:
        task_names = BENCHMARK_TASKS[benchmark]
        if len(task_names) == 1:
            metrics[benchmark] = dict(task_results.get(task_names[0], {}))
        else:
            metrics[benchmark] = {task: dict(task_results.get(task, {})) for task in task_names}
    return metrics


def run_benchmark(
    *,
    benchmarks: list[str],
    model_id: str | None = None,
    model: PreTrainedModel | None = None,
    tokenizer: PreTrainedTokenizerBase | None = None,
    device: str | None = None,
    batch_size: int | str = 8,
    num_fewshot: int | None = None,
    limit: int | float | None = None,
    trust_remote_code: bool = False,
) -> dict[str, Any]:
    """Evaluate a model on one or more benchmark suites and return per-task metrics.

    Accepts either ``model_id`` (loads a fresh model + tokenizer by name) or an
    already-loaded ``model`` + ``tokenizer`` pair (e.g. a fine-tuned model a
    caller already holds in memory) -- exactly one of the two must be supplied,
    so this can be reused as-is by the base-vs-fine-tuned comparison in
    ``evaluation/compare.py``.
    """
    if not benchmarks:
        raise BenchmarkError("benchmarks must contain at least one benchmark name.")
    task_names = _resolve_task_names(benchmarks)

    has_model_id = model_id is not None
    has_loaded_model = model is not None and tokenizer is not None
    if has_model_id == has_loaded_model:
        raise BenchmarkError("Provide either model_id, or both model and tokenizer -- not both.")

    lm_eval = _get_lm_eval()
    hflm_cls = _get_hflm_cls()
    resolved_device = device or _resolve_device()

    if model_id is not None:
        hflm = hflm_cls(
            pretrained=model_id,
            device=resolved_device,
            batch_size=batch_size,
            trust_remote_code=trust_remote_code,
        )
    else:
        hflm = hflm_cls(
            pretrained=model,
            tokenizer=tokenizer,
            batch_size=batch_size,
        )

    logger.info(
        "benchmark_run_start",
        benchmarks=list(benchmarks),
        tasks=task_names,
        model_id=model_id,
        num_fewshot=num_fewshot,
        limit=limit,
    )

    raw_results = lm_eval.simple_evaluate(
        model=hflm,
        tasks=task_names,
        num_fewshot=num_fewshot,
        batch_size=batch_size,
        device=resolved_device,
        limit=limit,
        log_samples=False,
    )

    metrics = _extract_metrics(raw_results, benchmarks)

    logger.info("benchmark_run_complete", benchmarks=list(benchmarks), metrics=metrics)

    return {
        "status": "completed",
        "model_id": model_id,
        "benchmarks": list(benchmarks),
        "metrics": metrics,
    }
