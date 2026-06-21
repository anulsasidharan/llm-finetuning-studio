from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from trainers.base_trainer import TrainerError
from trainers.sft_trainer import SFTTrainer

ALPACA_ROW = {"instruction": "Summarize this.", "input": "Some text.", "output": "A summary."}

SFT_CONFIG = {
    "learning_rate": 0.0002,
    "num_epochs": 1,
    "batch_size": 2,
    "max_seq_length": 512,
    "warmup_ratio": 0.03,
    "weight_decay": 0.0,
    "gradient_accumulation_steps": 1,
}


def _make_trainer(tmp_path: Path, **kwargs: Any) -> SFTTrainer:
    defaults = {
        "job_id": uuid4(),
        "base_model_id": "meta-llama/Meta-Llama-3-8B",
        "methodology": "sft",
        "training_config": SFT_CONFIG,
        "dataset_rows": [ALPACA_ROW],
        "output_dir": tmp_path,
        "dataset_format": "alpaca",
    }
    defaults.update(kwargs)
    return SFTTrainer(**defaults)


def test_sft_trainer_rejects_non_sft_methodology(tmp_path: Path) -> None:
    with pytest.raises(TrainerError, match="requires methodology='sft'"):
        _make_trainer(tmp_path, methodology="lora")


@patch("trainers.sft_trainer.get_hf_dataset_class")
@patch("trainers.sft_trainer._get_trl_sft_trainer")
@patch("transformers.AutoModelForCausalLM")
@patch("transformers.AutoTokenizer")
def test_sft_train_runs_trl_trainer_with_chatml_rows(
    mock_tokenizer_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_get_trl: MagicMock,
    mock_dataset_cls: MagicMock,
    tmp_path: Path,
) -> None:
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token = None
    mock_tokenizer.eos_token = "<eos>"
    mock_tokenizer.apply_chat_template.return_value = "<chatml-formatted>"
    mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer

    mock_model = MagicMock()
    mock_model_cls.from_pretrained.return_value = mock_model

    mock_train_dataset = MagicMock()
    mock_dataset_cls.return_value.from_list.return_value = mock_train_dataset

    mock_trl_trainer_cls = MagicMock()
    mock_trl_instance = MagicMock()
    mock_trl_instance.train.return_value = MagicMock(metrics={"train_loss": 0.42})
    mock_trl_trainer_cls.return_value = mock_trl_instance
    mock_get_trl.return_value = mock_trl_trainer_cls

    trainer = _make_trainer(tmp_path)
    result = trainer.train()

    mock_tokenizer_cls.from_pretrained.assert_called_once_with(
        "meta-llama/Meta-Llama-3-8B",
        trust_remote_code=False,
    )
    mock_model_cls.from_pretrained.assert_called_once()

    prepared_rows = trainer.prepare_dataset_rows()
    mock_dataset_cls.return_value.from_list.assert_called_once_with(prepared_rows)

    mock_trl_trainer_cls.assert_called_once()
    trl_kwargs = mock_trl_trainer_cls.call_args.kwargs
    assert trl_kwargs["model"] is mock_model
    assert trl_kwargs["tokenizer"] is mock_tokenizer
    assert trl_kwargs["train_dataset"] is mock_train_dataset
    assert trl_kwargs["max_seq_length"] == 512
    assert trl_kwargs["packing"] is False
    assert trl_kwargs["callbacks"] == []

    formatting_func = trl_kwargs["formatting_func"]
    sample_row = prepared_rows[0]
    assert formatting_func(sample_row) == "<chatml-formatted>"
    mock_tokenizer.apply_chat_template.assert_called_once_with(
        sample_row["messages"],
        tokenize=False,
        add_generation_prompt=False,
    )

    mock_trl_instance.train.assert_called_once()
    mock_trl_instance.save_model.assert_called_once_with(str(tmp_path / "final"))
    mock_tokenizer.save_pretrained.assert_called_once_with(str(tmp_path / "final"))

    assert result == {
        "status": "completed",
        "methodology": "sft",
        "job_id": trainer.job_id,
        "output_dir": str(tmp_path),
        "model_dir": str(tmp_path / "final"),
        "num_rows": 1,
        "metrics": {"train_loss": 0.42},
    }


@patch("trainers.sft_trainer.get_hf_dataset_class")
@patch("trainers.sft_trainer._get_trl_sft_trainer")
@patch("transformers.AutoModelForCausalLM")
@patch("transformers.AutoTokenizer")
def test_sft_train_passes_callbacks_to_trl_trainer(
    mock_tokenizer_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_get_trl: MagicMock,
    mock_dataset_cls: MagicMock,
    tmp_path: Path,
) -> None:
    callback = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token = "<pad>"
    mock_tokenizer.apply_chat_template.return_value = "text"
    mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer
    mock_model_cls.from_pretrained.return_value = MagicMock()
    mock_dataset_cls.return_value.from_list.return_value = MagicMock()

    mock_trl_trainer_cls = MagicMock()
    mock_trl_instance = MagicMock()
    mock_trl_instance.train.return_value = MagicMock(metrics={})
    mock_trl_trainer_cls.return_value = mock_trl_instance
    mock_get_trl.return_value = mock_trl_trainer_cls

    trainer = _make_trainer(tmp_path, callbacks=[callback])
    trainer.train()

    trl_kwargs = mock_trl_trainer_cls.call_args.kwargs
    assert trl_kwargs["callbacks"] == [callback]
