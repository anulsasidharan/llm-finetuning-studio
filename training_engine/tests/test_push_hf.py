from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from export.push_hf import PushHFError, push_to_hub


def _make_model_dir(tmp_path: Path) -> Path:
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    (model_dir / "config.json").write_text('{"model_type": "llama"}')
    return model_dir


def test_push_to_hub_raises_when_model_dir_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(PushHFError, match="model_dir does not exist"):
        push_to_hub(tmp_path / "nonexistent", "user/model")


def test_push_to_hub_raises_when_repo_id_empty(tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)
    with pytest.raises(PushHFError, match="repo_id must be a non-empty string"):
        push_to_hub(model_dir, "")


def test_push_to_hub_raises_when_repo_id_whitespace_only(tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)
    with pytest.raises(PushHFError, match="repo_id must be a non-empty string"):
        push_to_hub(model_dir, "   ")


@patch("export.push_hf._get_hf_api_cls")
def test_push_to_hub_success(mock_get_cls: MagicMock, tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)

    mock_commit_info = MagicMock()
    mock_commit_info.commit_url = "https://huggingface.co/user/model/commit/abc123"

    mock_api = MagicMock()
    mock_api.upload_folder.return_value = mock_commit_info

    mock_api_cls = MagicMock(return_value=mock_api)
    mock_get_cls.return_value = mock_api_cls

    result = push_to_hub(model_dir, "user/model", hf_token="hf_token_abc")

    mock_api_cls.assert_called_once_with(token="hf_token_abc")
    mock_api.create_repo.assert_called_once_with(
        repo_id="user/model",
        private=False,
        exist_ok=True,
        repo_type="model",
    )
    mock_api.upload_folder.assert_called_once_with(
        folder_path=str(model_dir),
        repo_id="user/model",
        repo_type="model",
        commit_message="Upload fine-tuned model via LLM Fine-Tuning Studio",
    )

    assert result == {
        "status": "completed",
        "model_dir": str(model_dir),
        "repo_id": "user/model",
        "repo_url": "https://huggingface.co/user/model",
        "commit_url": "https://huggingface.co/user/model/commit/abc123",
    }


@patch("export.push_hf._get_hf_api_cls")
def test_push_to_hub_private_flag(mock_get_cls: MagicMock, tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)

    mock_api = MagicMock()
    mock_api.upload_folder.return_value = MagicMock(
        commit_url="https://huggingface.co/user/private-model/commit/def456"
    )
    mock_get_cls.return_value = MagicMock(return_value=mock_api)

    push_to_hub(model_dir, "user/private-model", private=True)

    mock_api.create_repo.assert_called_once_with(
        repo_id="user/private-model",
        private=True,
        exist_ok=True,
        repo_type="model",
    )


@patch("export.push_hf._get_hf_api_cls")
def test_push_to_hub_custom_commit_message(mock_get_cls: MagicMock, tmp_path: Path) -> None:
    model_dir = _make_model_dir(tmp_path)

    mock_api = MagicMock()
    mock_api.upload_folder.return_value = MagicMock(
        commit_url="https://huggingface.co/u/m/commit/x"
    )
    mock_get_cls.return_value = MagicMock(return_value=mock_api)

    push_to_hub(model_dir, "user/model", commit_message="My custom message")

    _, kwargs = mock_api.upload_folder.call_args
    assert kwargs["commit_message"] == "My custom message"


@patch("export.push_hf._get_hf_api_cls")
def test_push_to_hub_default_commit_message_when_none(
    mock_get_cls: MagicMock, tmp_path: Path
) -> None:
    model_dir = _make_model_dir(tmp_path)

    mock_api = MagicMock()
    mock_api.upload_folder.return_value = MagicMock(
        commit_url="https://huggingface.co/u/m/commit/y"
    )
    mock_get_cls.return_value = MagicMock(return_value=mock_api)

    push_to_hub(model_dir, "user/model")

    _, kwargs = mock_api.upload_folder.call_args
    assert "LLM Fine-Tuning Studio" in kwargs["commit_message"]
