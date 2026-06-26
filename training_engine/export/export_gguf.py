"""Export a HuggingFace model directory to GGUF format for llama.cpp inference.

Calls the ``convert_hf_to_gguf.py`` script from the llama.cpp project via
subprocess.  The script path is resolved from (in priority order):

1. The ``llama_cpp_path`` function parameter — either the full path to
   ``convert_hf_to_gguf.py`` or the llama.cpp repository root directory
   that contains it.
2. The ``LLAMA_CPP_CONVERT_SCRIPT`` environment variable (full path to the
   conversion script).

Raises ``ExportGGUFError`` with a descriptive message if the script cannot be
located or if the conversion subprocess exits with a non-zero status code.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class ExportGGUFError(ValueError):
    """Raised when GGUF export inputs or configuration are invalid."""


SUPPORTED_QUANT_TYPES: frozenset[str] = frozenset(
    {
        "f32",
        "f16",
        "q8_0",
        "q6_k",
        "q5_k_m",
        "q5_0",
        "q4_k_m",
        "q4_0",
        "q3_k_m",
        "q2_k",
    }
)


def _resolve_convert_script(llama_cpp_path: str | Path | None) -> Path:
    """Locate the llama.cpp convert_hf_to_gguf.py script.

    Raises ``ExportGGUFError`` if the script cannot be found.
    """
    if llama_cpp_path is not None:
        p = Path(llama_cpp_path)
        if p.is_file():
            return p
        candidate = p / "convert_hf_to_gguf.py"
        if candidate.is_file():
            return candidate
        raise ExportGGUFError(
            f"llama_cpp_path '{p}' is neither convert_hf_to_gguf.py itself "
            "nor a directory containing it."
        )

    env_val = os.environ.get("LLAMA_CPP_CONVERT_SCRIPT")
    if env_val:
        script = Path(env_val)
        if script.is_file():
            return script
        raise ExportGGUFError(
            f"LLAMA_CPP_CONVERT_SCRIPT env var points to '{script}' which does not exist."
        )

    raise ExportGGUFError(
        "llama.cpp convert script not found. "
        "Pass llama_cpp_path= pointing to convert_hf_to_gguf.py or a llama.cpp "
        "checkout directory, or set the LLAMA_CPP_CONVERT_SCRIPT environment variable."
    )


def _run_convert_subprocess(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True)


def export_gguf(
    model_dir: str | Path,
    output_dir: str | Path,
    *,
    quantization_type: str = "q4_k_m",
    llama_cpp_path: str | Path | None = None,
    model_name: str | None = None,
) -> dict[str, Any]:
    """Convert a HuggingFace model directory to GGUF format.

    Parameters
    ----------
    model_dir:
        Directory containing the saved HuggingFace model (``config.json``,
        ``*.safetensors``, tokenizer files, …).  Typically produced by
        ``merge_lora`` or a trainer's ``save_pretrained`` call.
    output_dir:
        Directory where the ``.gguf`` file will be written.  Created
        automatically if it does not exist.
    quantization_type:
        GGUF quantization type passed to ``--outtype``.  Supported values:
        ``f32``, ``f16``, ``q8_0``, ``q6_k``, ``q5_k_m``, ``q5_0``,
        ``q4_k_m`` (default), ``q4_0``, ``q3_k_m``, ``q2_k``.
    llama_cpp_path:
        Path to ``convert_hf_to_gguf.py`` directly, or to the llama.cpp
        repository root directory that contains it.  When *None*, the
        ``LLAMA_CPP_CONVERT_SCRIPT`` environment variable is consulted.
    model_name:
        Base name for the output file (without extension).  Defaults to
        the name of ``model_dir``.

    Returns
    -------
    dict with keys ``status``, ``model_dir``, ``output_dir``,
    ``gguf_path``, ``quantization_type``.
    """
    model_path = Path(model_dir)
    output_path = Path(output_dir)

    if not model_path.exists():
        raise ExportGGUFError(f"model_dir does not exist: {model_path}")

    if quantization_type not in SUPPORTED_QUANT_TYPES:
        raise ExportGGUFError(
            f"Unsupported quantization_type '{quantization_type}'. "
            f"Supported types: {sorted(SUPPORTED_QUANT_TYPES)}"
        )

    convert_script = _resolve_convert_script(llama_cpp_path)
    output_path.mkdir(parents=True, exist_ok=True)

    resolved_name = model_name or model_path.name
    gguf_filename = f"{resolved_name}-{quantization_type}.gguf"
    gguf_path = output_path / gguf_filename

    cmd = [
        sys.executable,
        str(convert_script),
        str(model_path),
        "--outtype",
        quantization_type,
        "--outfile",
        str(gguf_path),
    ]

    logger.info(
        "export_gguf_start",
        model_dir=str(model_path),
        output_dir=str(output_path),
        quantization_type=quantization_type,
        gguf_path=str(gguf_path),
    )

    result = _run_convert_subprocess(cmd)

    if result.returncode != 0:
        raise ExportGGUFError(
            f"GGUF conversion failed (exit {result.returncode}).\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    logger.info(
        "export_gguf_complete",
        gguf_path=str(gguf_path),
        quantization_type=quantization_type,
    )

    return {
        "status": "completed",
        "model_dir": str(model_path),
        "output_dir": str(output_path),
        "gguf_path": str(gguf_path),
        "quantization_type": quantization_type,
    }
