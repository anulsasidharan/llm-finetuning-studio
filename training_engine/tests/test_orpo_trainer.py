from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from trainers.base_trainer import TrainerError
from trainers.orpo_trainer import ORPOTrainer

PAIR_ROW = {
    "prompt": "What is the capital of France?",
    "chosen": "The capital of France is Paris.",
    "rejected": "I don't know.",
}

ORPO_CONFIG = {
    "learning_rate": 0.0002,
    "num_epochs": 1,
    "batch_size": 2,
    "max_seq_length": 512,
    "warmup_ratio": 0.03,
    "weight_decay": 0.0,
    "gradient_accumulation_steps": 1,
    "beta": 0.1,
}


def _make_trainer(tmp_path: Path, **kwargs: Any) -> ORPOTrainer:
    defaults = {
        "job_id": uuid4(),
        "base_model_id": "meta-llama/Meta-Llama-3-8B",
        "methodology": "orpo",
        "training_config": ORPO_CONFIG,
        "dataset_rows": [PAIR_ROW],
        "output_dir": tmp_path,
    }
    defaults.update(kwargs)
    return ORPOTrainer(**defaults)


def test_orpo_trainer_rejects_non_orpo_methodology(tmp_path: Path) -> None:
    with pytest.raises(TrainerError, match="requires methodology='orpo'"):
        _make_trainer(tmp_path, methodology="sft")


def test_orpo_trainer_rejects_missing_beta(tmp_path: Path) -> None:
    config = {
        "learning_rate": 0.0002,
        "num_epochs": 1,
        "batch_size": 2,
    }
    with pytest.raises(TrainerError, match="requires beta"):
        _make_trainer(tmp_path, training_config=config)


def test_orpo_trainer_rejects_row_missing_pair_keys(tmp_path: Path) -> None:
    trainer = _make_trainer(tmp_path, dataset_rows=[{"prompt": "hi", "chosen": "hello"}])
    with pytest.raises(TrainerError, match="missing required keys"):
        trainer.prepare_preference_rows()


@patch("trainers.orpo_trainer.get_hf_dataset_class")
@patch("trainers.orpo_trainer._get_trl_orpo_config")
@patch("trainers.orpo_trainer._get_trl_orpo_trainer")
@patch("transformers.AutoModelForCausalLM")
@patch("transformers.AutoTokenizer")
def test_orpo_train_loads_single_model_and_runs_trl_trainer(
    mock_tokenizer_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_get_trl_trainer: MagicMock,
    mock_get_trl_config: MagicMock,
    mock_dataset_cls: MagicMock,
    tmp_path: Path,
) -> None:
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token = None
    mock_tokenizer.eos_token = "<eos>"
    mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer

    mock_model = MagicMock()
    mock_model_cls.from_pretrained.return_value = mock_model

    mock_train_dataset = MagicMock()
    mock_dataset_cls.return_value.from_list.return_value = mock_train_dataset

    mock_orpo_config_cls = MagicMock()
    mock_orpo_args = MagicMock()
    mock_orpo_config_cls.return_value = mock_orpo_args
    mock_get_trl_config.return_value = mock_orpo_config_cls

    mock_trl_trainer_cls = MagicMock()
    mock_trl_instance = MagicMock()
    mock_trl_instance.train.return_value = MagicMock(metrics={"train_loss": 0.18})
    mock_trl_trainer_cls.return_value = mock_trl_instance
    mock_get_trl_trainer.return_value = mock_trl_trainer_cls

    trainer = _make_trainer(tmp_path)
    result = trainer.train()

    assert mock_model_cls.from_pretrained.call_count == 1

    mock_orpo_config_cls.assert_called_once()
    config_kwargs = mock_orpo_config_cls.call_args.kwargs
    assert config_kwargs["beta"] == 0.1
    assert config_kwargs["max_length"] == 512
    assert config_kwargs["max_prompt_length"] == 256

    mock_trl_trainer_cls.assert_called_once()
    trl_kwargs = mock_trl_trainer_cls.call_args.kwargs
    assert trl_kwargs["model"] is mock_model
    assert trl_kwargs["args"] is mock_orpo_args
    assert trl_kwargs["tokenizer"] is mock_tokenizer
    assert trl_kwargs["train_dataset"] is mock_train_dataset
    assert "ref_model" not in trl_kwargs
    assert "beta" not in trl_kwargs

    mock_trl_instance.train.assert_called_once()
    mock_trl_instance.save_model.assert_called_once_with(str(tmp_path / "final"))
    mock_tokenizer.save_pretrained.assert_called_once_with(str(tmp_path / "final"))

    assert result == {
        "status": "completed",
        "methodology": "orpo",
        "job_id": trainer.job_id,
        "output_dir": str(tmp_path),
        "model_dir": str(tmp_path / "final"),
        "num_rows": 1,
        "metrics": {"train_loss": 0.18},
    }


@patch("trainers.orpo_trainer.get_hf_dataset_class")
@patch("trainers.orpo_trainer._get_trl_orpo_config")
@patch("trainers.orpo_trainer._get_trl_orpo_trainer")
@patch("transformers.AutoModelForCausalLM")
@patch("transformers.AutoTokenizer")
def test_orpo_train_passes_callbacks_to_trl_trainer(
    mock_tokenizer_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_get_trl_trainer: MagicMock,
    mock_get_trl_config: MagicMock,
    mock_dataset_cls: MagicMock,
    tmp_path: Path,
) -> None:
    callback = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token = "<pad>"
    mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer
    mock_model_cls.from_pretrained.return_value = MagicMock()
    mock_dataset_cls.return_value.from_list.return_value = MagicMock()
    mock_get_trl_config.return_value = MagicMock()

    mock_trl_trainer_cls = MagicMock()
    mock_trl_instance = MagicMock()
    mock_trl_instance.train.return_value = MagicMock(metrics={})
    mock_trl_trainer_cls.return_value = mock_trl_instance
    mock_get_trl_trainer.return_value = mock_trl_trainer_cls

    trainer = _make_trainer(tmp_path, callbacks=[callback])
    trainer.train()

    trl_kwargs = mock_trl_trainer_cls.call_args.kwargs
    assert trl_kwargs["callbacks"] == [callback]
