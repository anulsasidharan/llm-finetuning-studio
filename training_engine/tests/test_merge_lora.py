from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from export.merge_lora import MergeLoRAError, merge_lora


def _make_adapter_dir(tmp_path: Path, base_model_id: str = "meta-llama/Meta-Llama-3-8B") -> Path:
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    config = {"base_model_name_or_path": base_model_id, "r": 8, "lora_alpha": 16}
    (adapter_dir / "adapter_config.json").write_text(json.dumps(config))
    return adapter_dir


def test_merge_lora_raises_when_adapter_dir_does_not_exist(tmp_path: Path) -> None:
    with pytest.raises(MergeLoRAError, match="adapter_dir does not exist"):
        merge_lora(tmp_path / "nonexistent", tmp_path / "output")


def test_merge_lora_raises_when_adapter_config_missing(tmp_path: Path) -> None:
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    with pytest.raises(MergeLoRAError, match="adapter_config.json not found"):
        merge_lora(adapter_dir, tmp_path / "output")


def test_merge_lora_raises_when_no_base_model_id(tmp_path: Path) -> None:
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    (adapter_dir / "adapter_config.json").write_text(json.dumps({"r": 8}))
    with pytest.raises(MergeLoRAError, match="base_model_id not supplied"):
        merge_lora(adapter_dir, tmp_path / "output")


@patch("export.merge_lora._get_peft_model_cls")
@patch("export.merge_lora._load_base_model_and_tokenizer")
def test_merge_lora_success(
    mock_load: MagicMock,
    mock_get_peft: MagicMock,
    tmp_path: Path,
) -> None:
    adapter_dir = _make_adapter_dir(tmp_path)
    output_dir = tmp_path / "output"

    mock_base_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_load.return_value = (mock_base_model, mock_tokenizer)

    mock_merged_model = MagicMock()
    mock_peft_instance = MagicMock()
    mock_peft_instance.merge_and_unload.return_value = mock_merged_model

    mock_peft_model_cls = MagicMock()
    mock_peft_model_cls.from_pretrained.return_value = mock_peft_instance
    mock_get_peft.return_value = mock_peft_model_cls

    result = merge_lora(adapter_dir, output_dir)

    mock_load.assert_called_once_with("meta-llama/Meta-Llama-3-8B", trust_remote_code=False)
    mock_peft_model_cls.from_pretrained.assert_called_once_with(mock_base_model, str(adapter_dir))
    mock_peft_instance.merge_and_unload.assert_called_once()
    mock_merged_model.save_pretrained.assert_called_once_with(str(output_dir / "merged"))
    mock_tokenizer.save_pretrained.assert_called_once_with(str(output_dir / "merged"))

    assert result == {
        "status": "completed",
        "adapter_dir": str(adapter_dir),
        "output_dir": str(output_dir),
        "base_model_id": "meta-llama/Meta-Llama-3-8B",
        "merged_model_dir": str(output_dir / "merged"),
    }


@patch("export.merge_lora._get_peft_model_cls")
@patch("export.merge_lora._load_base_model_and_tokenizer")
def test_merge_lora_explicit_base_model_id_overrides_config(
    mock_load: MagicMock,
    mock_get_peft: MagicMock,
    tmp_path: Path,
) -> None:
    adapter_dir = _make_adapter_dir(tmp_path, base_model_id="config-model")
    output_dir = tmp_path / "output"

    mock_load.return_value = (MagicMock(), MagicMock())
    mock_peft_cls = MagicMock()
    mock_peft_cls.from_pretrained.return_value.merge_and_unload.return_value = MagicMock()
    mock_get_peft.return_value = mock_peft_cls

    result = merge_lora(adapter_dir, output_dir, base_model_id="explicit-model")

    mock_load.assert_called_once_with("explicit-model", trust_remote_code=False)
    assert result["base_model_id"] == "explicit-model"


@patch("export.merge_lora._get_peft_model_cls")
@patch("export.merge_lora._load_base_model_and_tokenizer")
def test_merge_lora_passes_trust_remote_code(
    mock_load: MagicMock,
    mock_get_peft: MagicMock,
    tmp_path: Path,
) -> None:
    adapter_dir = _make_adapter_dir(tmp_path)
    output_dir = tmp_path / "output"

    mock_load.return_value = (MagicMock(), MagicMock())
    mock_peft_cls = MagicMock()
    mock_peft_cls.from_pretrained.return_value.merge_and_unload.return_value = MagicMock()
    mock_get_peft.return_value = mock_peft_cls

    merge_lora(adapter_dir, output_dir, trust_remote_code=True)

    mock_load.assert_called_once_with("meta-llama/Meta-Llama-3-8B", trust_remote_code=True)
