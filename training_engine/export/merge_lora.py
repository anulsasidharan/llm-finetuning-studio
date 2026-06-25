"""Merge a PEFT LoRA adapter into its base model, producing a standalone merged model.

The saved LoRA/QLoRA training artifacts at ``adapter_dir`` contain only the adapter
weights (``adapter_model.safetensors`` + ``adapter_config.json``).  ``merge_lora``
loads the base model, wraps it with the adapter via ``peft.PeftModel.from_pretrained``,
calls ``.merge_and_unload()`` to fold the adapter weights in, and saves a
self-contained model + tokenizer to ``<output_dir>/merged``.

The base model id can be supplied explicitly (``base_model_id``); if omitted it is read
from ``adapter_config.json``'s ``base_model_name_or_path`` field, which PEFT saves
automatically during ``trainer.save_model()``.

Heavy imports (peft, torch, transformers) are lazy so the module is importable in unit
tests without those packages installed — same pattern as all trainers.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class MergeLoRAError(ValueError):
    """Raised when LoRA merge inputs or artifacts are invalid."""


def _read_adapter_config(adapter_dir: Path) -> dict[str, Any]:
    config_path = adapter_dir / "adapter_config.json"
    if not config_path.exists():
        raise MergeLoRAError(
            f"adapter_config.json not found in {adapter_dir}. "
            "Ensure adapter_dir points to a PEFT-saved adapter directory."
        )
    with config_path.open() as fh:
        return json.load(fh)


def _get_peft_model_cls() -> type:
    from peft import PeftModel

    return PeftModel


def _load_base_model_and_tokenizer(
    base_model_id: str,
    *,
    trust_remote_code: bool,
) -> tuple[Any, Any]:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    dtype = torch.float16 if device == "cuda" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=dtype,
        device_map="auto" if device == "cuda" else None,
        trust_remote_code=trust_remote_code,
    )
    tokenizer = AutoTokenizer.from_pretrained(base_model_id, trust_remote_code=trust_remote_code)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    return model, tokenizer


def merge_lora(
    adapter_dir: str | Path,
    output_dir: str | Path,
    *,
    base_model_id: str | None = None,
    trust_remote_code: bool = False,
) -> dict[str, Any]:
    """Merge LoRA adapter weights into the base model and save a standalone model.

    Parameters
    ----------
    adapter_dir:
        Directory produced by ``LoRATrainer`` / ``QLoRATrainer`` (contains
        ``adapter_config.json`` and ``adapter_model.safetensors``).
    output_dir:
        Root directory for output.  The merged model is saved at
        ``<output_dir>/merged``.
    base_model_id:
        HuggingFace model id (or local path) for the base model.  If omitted,
        read from ``adapter_config.json``'s ``base_model_name_or_path`` field.
    trust_remote_code:
        Passed through to every ``from_pretrained`` call.

    Returns
    -------
    dict with keys ``status``, ``adapter_dir``, ``output_dir``, ``base_model_id``,
    ``merged_model_dir``.
    """
    adapter_path = Path(adapter_dir)
    output_path = Path(output_dir)

    if not adapter_path.exists():
        raise MergeLoRAError(f"adapter_dir does not exist: {adapter_path}")

    adapter_config = _read_adapter_config(adapter_path)
    resolved_base_model_id = base_model_id or adapter_config.get("base_model_name_or_path")
    if not resolved_base_model_id:
        raise MergeLoRAError(
            "base_model_id not supplied and not found in adapter_config.json "
            f"(keys present: {sorted(adapter_config.keys())})."
        )

    output_path.mkdir(parents=True, exist_ok=True)
    merged_model_dir = output_path / "merged"
    merged_model_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "merge_lora_start",
        adapter_dir=str(adapter_path),
        output_dir=str(output_path),
        base_model_id=resolved_base_model_id,
    )

    base_model, tokenizer = _load_base_model_and_tokenizer(
        resolved_base_model_id, trust_remote_code=trust_remote_code
    )

    PeftModel = _get_peft_model_cls()
    peft_model = PeftModel.from_pretrained(base_model, str(adapter_path))
    merged_model = peft_model.merge_and_unload()

    merged_model.save_pretrained(str(merged_model_dir))
    tokenizer.save_pretrained(str(merged_model_dir))

    logger.info(
        "merge_lora_complete",
        merged_model_dir=str(merged_model_dir),
        base_model_id=resolved_base_model_id,
    )

    return {
        "status": "completed",
        "adapter_dir": str(adapter_path),
        "output_dir": str(output_path),
        "base_model_id": resolved_base_model_id,
        "merged_model_dir": str(merged_model_dir),
    }
