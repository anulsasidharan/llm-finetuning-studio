"""Import HuggingFace ``datasets`` despite the local ``datasets/`` package name collision."""

from __future__ import annotations

import importlib
import sys
from functools import lru_cache
from types import ModuleType


def _training_engine_paths() -> tuple[str, ...]:
    blocked: list[str] = []
    for entry in sys.path:
        if not entry:
            continue
        normalized = entry.replace("\\", "/").rstrip("/")
        if normalized.endswith("/training_engine"):
            blocked.append(entry)
    return tuple(blocked)


@lru_cache(maxsize=1)
def ensure_hf_datasets_loaded() -> ModuleType:
    """Load the pip-installed HuggingFace ``datasets`` package for TRL imports."""
    existing = sys.modules.get("datasets")
    if existing is not None and hasattr(existing, "Dataset"):
        return existing

    preserved = {key: sys.modules[key] for key in list(sys.modules) if key.startswith("datasets.")}

    sys.modules.pop("datasets", None)

    blocked = _training_engine_paths()
    original_path = list(sys.path)
    try:
        sys.path = [path for path in sys.path if path not in blocked]
        hf_datasets = importlib.import_module("datasets")
    finally:
        sys.path = original_path
        for key, module in preserved.items():
            sys.modules[key] = module

    if not hasattr(hf_datasets, "Dataset"):
        raise ImportError("Failed to load HuggingFace datasets package")

    sys.modules["datasets"] = hf_datasets
    return hf_datasets


def get_hf_dataset_class() -> type:
    """Return HuggingFace ``datasets.Dataset``."""
    return ensure_hf_datasets_loaded().Dataset
