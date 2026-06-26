"""Push a saved model directory to HuggingFace Hub.

Accepts any local model directory (a self-contained merged model produced by
``merge_lora``, a LoRA adapter dir, an SFT checkpoint, etc.) and uploads it to
the HuggingFace Hub under ``repo_id``.  The repository is created automatically
if it does not yet exist.

Heavy imports (huggingface_hub) are lazy so the module is importable in unit
tests without the package installed — same pattern as merge_lora.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


class PushHFError(ValueError):
    """Raised when pushing to HuggingFace Hub fails due to invalid inputs."""


def _get_hf_api_cls() -> type:
    from huggingface_hub import HfApi

    return HfApi


def push_to_hub(
    model_dir: str | Path,
    repo_id: str,
    *,
    hf_token: str | None = None,
    private: bool = False,
    commit_message: str | None = None,
    trust_remote_code: bool = False,
) -> dict[str, Any]:
    """Upload a local model directory to the HuggingFace Hub.

    Parameters
    ----------
    model_dir:
        Local directory containing saved model files (``config.json``,
        ``*.safetensors``, tokenizer files, …).  Produced by ``merge_lora``
        or a trainer's ``save_pretrained`` call.
    repo_id:
        HuggingFace Hub repository identifier, e.g. ``"username/model-name"``.
        The repository is created with ``exist_ok=True`` if it does not exist.
    hf_token:
        HuggingFace access token.  When *None*, the ``huggingface_hub`` library
        falls back to the token stored by ``huggingface-cli login`` or the
        ``HUGGING_FACE_HUB_TOKEN`` environment variable.
    private:
        Create the repository as private when it does not yet exist.  Has no
        effect on an already-existing repository.
    commit_message:
        Commit message for the uploaded revision.  Defaults to a generic
        description when not provided.
    trust_remote_code:
        Included for API symmetry with ``merge_lora``; not consumed by the
        file-upload path.

    Returns
    -------
    dict with keys ``status``, ``model_dir``, ``repo_id``, ``repo_url``,
    ``commit_url``.
    """
    model_path = Path(model_dir)

    if not model_path.exists():
        raise PushHFError(f"model_dir does not exist: {model_path}")

    if not repo_id or not repo_id.strip():
        raise PushHFError("repo_id must be a non-empty string, e.g. 'username/model-name'.")

    resolved_commit_message = commit_message or "Upload fine-tuned model via LLM Fine-Tuning Studio"

    HfApi = _get_hf_api_cls()
    api = HfApi(token=hf_token)

    logger.info(
        "push_to_hub_start",
        model_dir=str(model_path),
        repo_id=repo_id,
        private=private,
    )

    api.create_repo(
        repo_id=repo_id,
        private=private,
        exist_ok=True,
        repo_type="model",
    )

    commit_info = api.upload_folder(
        folder_path=str(model_path),
        repo_id=repo_id,
        repo_type="model",
        commit_message=resolved_commit_message,
    )

    repo_url = f"https://huggingface.co/{repo_id}"

    logger.info(
        "push_to_hub_complete",
        repo_id=repo_id,
        repo_url=repo_url,
        commit_url=commit_info.commit_url,
    )

    return {
        "status": "completed",
        "model_dir": str(model_path),
        "repo_id": repo_id,
        "repo_url": repo_url,
        "commit_url": commit_info.commit_url,
    }
