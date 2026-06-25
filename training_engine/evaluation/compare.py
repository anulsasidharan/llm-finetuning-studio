"""Compare a base model against its fine-tuned counterpart: side-by-side generations + optional benchmark deltas."""

from __future__ import annotations

from typing import Any

import structlog
from transformers import PreTrainedModel, PreTrainedTokenizerBase

from evaluation.benchmark import run_benchmark

logger = structlog.get_logger()


class CompareError(ValueError):
    """Raised when comparison inputs are invalid."""


def _resolve_device() -> str:
    import torch

    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def _load_model_and_tokenizer(
    model_id: str,
    *,
    device: str,
    trust_remote_code: bool,
) -> tuple[PreTrainedModel, PreTrainedTokenizerBase]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=trust_remote_code)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.float16 if device == "cuda" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=trust_remote_code,
    )
    if device != "cuda":
        model.to(device)
    return model, tokenizer


def _resolve_side(
    *,
    label: str,
    model_id: str | None,
    model: PreTrainedModel | None,
    tokenizer: PreTrainedTokenizerBase | None,
    device: str,
    trust_remote_code: bool,
) -> tuple[PreTrainedModel, PreTrainedTokenizerBase, str | None]:
    """Resolve one side (base or finetuned) to a loaded (model, tokenizer) pair.

    Accepts either ``{label}_model_id`` (loaded fresh here) or an already-loaded
    ``{label}_model``/``{label}_tokenizer`` pair -- the same dual-input contract
    ``run_benchmark`` uses, so whichever way a side is supplied, the resulting
    loaded model/tokenizer can be passed straight into ``run_benchmark`` via its
    loaded-model branch later without loading it a second time.
    """
    has_model_id = model_id is not None
    has_loaded_model = model is not None and tokenizer is not None
    if has_model_id == has_loaded_model:
        raise CompareError(
            f"Provide either {label}_model_id, or both {label}_model and "
            f"{label}_tokenizer -- not both."
        )
    if model_id is not None:
        loaded_model, loaded_tokenizer = _load_model_and_tokenizer(
            model_id, device=device, trust_remote_code=trust_remote_code
        )
        return loaded_model, loaded_tokenizer, model_id
    return model, tokenizer, None


def _generate(
    model: PreTrainedModel,
    tokenizer: PreTrainedTokenizerBase,
    prompt: str,
    *,
    max_new_tokens: int,
) -> str:
    device = next(model.parameters()).device
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    output_ids = model.generate(
        **inputs,
        max_new_tokens=max_new_tokens,
        pad_token_id=tokenizer.pad_token_id,
    )
    generated_ids = output_ids[0][inputs["input_ids"].shape[-1] :]
    return tokenizer.decode(generated_ids, skip_special_tokens=True)


def _diff_metrics(
    base_metrics: dict[str, Any], finetuned_metrics: dict[str, Any]
) -> dict[str, Any]:
    """Recursively compute finetuned-minus-base deltas for numeric leaves shared by both sides."""
    diff: dict[str, Any] = {}
    for key, finetuned_value in finetuned_metrics.items():
        base_value = base_metrics.get(key)
        if isinstance(finetuned_value, dict) and isinstance(base_value, dict):
            diff[key] = _diff_metrics(base_value, finetuned_value)
        elif isinstance(finetuned_value, int | float) and isinstance(base_value, int | float):
            diff[key] = finetuned_value - base_value
    return diff


def compare_models(
    *,
    prompts: list[str],
    base_model_id: str | None = None,
    base_model: PreTrainedModel | None = None,
    base_tokenizer: PreTrainedTokenizerBase | None = None,
    finetuned_model_id: str | None = None,
    finetuned_model: PreTrainedModel | None = None,
    finetuned_tokenizer: PreTrainedTokenizerBase | None = None,
    benchmarks: list[str] | None = None,
    device: str | None = None,
    max_new_tokens: int = 256,
    num_fewshot: int | None = None,
    limit: int | float | None = None,
    trust_remote_code: bool = False,
) -> dict[str, Any]:
    """Generate side-by-side completions from a base and fine-tuned model, plus optional benchmark deltas.

    Each side accepts either a ``*_model_id`` or an already-loaded ``*_model``/
    ``*_tokenizer`` pair, mirroring ``run_benchmark``'s dual-input contract. When
    ``benchmarks`` is given, both sides' already-loaded model/tokenizer are reused
    as-is for ``run_benchmark`` (via its loaded-model branch) instead of letting it
    reload either model from disk a second time.
    """
    if not prompts:
        raise CompareError("prompts must contain at least one prompt.")

    resolved_device = device or _resolve_device()

    base_loaded_model, base_loaded_tokenizer, resolved_base_model_id = _resolve_side(
        label="base",
        model_id=base_model_id,
        model=base_model,
        tokenizer=base_tokenizer,
        device=resolved_device,
        trust_remote_code=trust_remote_code,
    )
    finetuned_loaded_model, finetuned_loaded_tokenizer, resolved_finetuned_model_id = _resolve_side(
        label="finetuned",
        model_id=finetuned_model_id,
        model=finetuned_model,
        tokenizer=finetuned_tokenizer,
        device=resolved_device,
        trust_remote_code=trust_remote_code,
    )

    logger.info(
        "compare_run_start",
        base_model_id=resolved_base_model_id,
        finetuned_model_id=resolved_finetuned_model_id,
        num_prompts=len(prompts),
        benchmarks=benchmarks,
    )

    completions = [
        {
            "prompt": prompt,
            "base_completion": _generate(
                base_loaded_model, base_loaded_tokenizer, prompt, max_new_tokens=max_new_tokens
            ),
            "finetuned_completion": _generate(
                finetuned_loaded_model,
                finetuned_loaded_tokenizer,
                prompt,
                max_new_tokens=max_new_tokens,
            ),
        }
        for prompt in prompts
    ]

    result: dict[str, Any] = {
        "status": "completed",
        "base_model_id": resolved_base_model_id,
        "finetuned_model_id": resolved_finetuned_model_id,
        "completions": completions,
    }

    if benchmarks:
        base_benchmark = run_benchmark(
            benchmarks=benchmarks,
            model=base_loaded_model,
            tokenizer=base_loaded_tokenizer,
            device=resolved_device,
            num_fewshot=num_fewshot,
            limit=limit,
        )
        finetuned_benchmark = run_benchmark(
            benchmarks=benchmarks,
            model=finetuned_loaded_model,
            tokenizer=finetuned_loaded_tokenizer,
            device=resolved_device,
            num_fewshot=num_fewshot,
            limit=limit,
        )
        result["benchmarks"] = {
            "base": base_benchmark["metrics"],
            "finetuned": finetuned_benchmark["metrics"],
            "delta": _diff_metrics(base_benchmark["metrics"], finetuned_benchmark["metrics"]),
        }

    logger.info(
        "compare_run_complete",
        base_model_id=resolved_base_model_id,
        finetuned_model_id=resolved_finetuned_model_id,
    )

    return result
