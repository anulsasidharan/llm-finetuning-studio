from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from trainers.base_trainer import BaseTrainer, TrainerConfig, TrainerError

ALPACA_ROW = {"instruction": "Summarize this.", "input": "Some text.", "output": "A summary."}
LORA_CONFIG = {
    "learning_rate": 0.0002,
    "num_epochs": 3,
    "batch_size": 4,
    "warmup_ratio": 0.03,
    "weight_decay": 0.0,
    "max_seq_length": 2048,
    "gradient_accumulation_steps": 1,
    "lora_r": 8,
    "lora_alpha": 16,
}


class DummyTrainer(BaseTrainer):
    def train(self) -> dict[str, Any]:
        return {
            "status": "completed",
            "output_dir": str(self.output_dir),
            "num_rows": len(self.prepare_dataset_rows()),
        }


def test_trainer_config_from_dict_parses_flat_config() -> None:
    config = TrainerConfig.from_dict(LORA_CONFIG)
    assert config.learning_rate == 0.0002
    assert config.num_epochs == 3
    assert config.batch_size == 4
    assert config.lora_r == 8
    assert config.lora_alpha == 16


def test_trainer_config_from_dict_applies_defaults() -> None:
    config = TrainerConfig.from_dict({"learning_rate": 1e-4, "num_epochs": 1, "batch_size": 2})
    assert config.warmup_ratio == 0.03
    assert config.max_seq_length == 2048
    assert config.gradient_accumulation_steps == 1


def test_trainer_config_from_dict_raises_on_missing_required_keys() -> None:
    with pytest.raises(TrainerError, match="missing required keys"):
        TrainerConfig.from_dict({"learning_rate": 1e-4})


def test_base_trainer_cannot_be_instantiated_directly(tmp_path: Path) -> None:
    with pytest.raises(TypeError):
        BaseTrainer(  # type: ignore[abstract]
            job_id=uuid4(),
            base_model_id="meta-llama/Meta-Llama-3-8B",
            methodology="lora",
            training_config=LORA_CONFIG,
            dataset_rows=[ALPACA_ROW],
            output_dir=tmp_path,
        )


def test_base_trainer_rejects_unsupported_methodology(tmp_path: Path) -> None:
    with pytest.raises(TrainerError, match="Unsupported methodology"):
        DummyTrainer(
            job_id=uuid4(),
            base_model_id="meta-llama/Meta-Llama-3-8B",
            methodology="invalid",
            training_config=LORA_CONFIG,
            dataset_rows=[ALPACA_ROW],
            output_dir=tmp_path,
        )


def test_base_trainer_rejects_empty_dataset(tmp_path: Path) -> None:
    with pytest.raises(TrainerError, match="at least one example"):
        DummyTrainer(
            job_id=uuid4(),
            base_model_id="meta-llama/Meta-Llama-3-8B",
            methodology="lora",
            training_config=LORA_CONFIG,
            dataset_rows=[],
            output_dir=tmp_path,
        )


def test_build_training_arguments_maps_config(tmp_path: Path) -> None:
    trainer = DummyTrainer(
        job_id=uuid4(),
        base_model_id="meta-llama/Meta-Llama-3-8B",
        methodology="lora",
        training_config=LORA_CONFIG,
        dataset_rows=[ALPACA_ROW],
        output_dir=tmp_path,
    )
    args = trainer.build_training_arguments()
    assert args.num_train_epochs == 3
    assert args.per_device_train_batch_size == 4
    assert args.learning_rate == 0.0002
    assert args.warmup_ratio == 0.03
    assert args.weight_decay == 0.0
    assert args.gradient_accumulation_steps == 1
    assert args.output_dir == str(tmp_path)


def test_prepare_dataset_rows_normalizes_alpaca_to_chatml(tmp_path: Path) -> None:
    trainer = DummyTrainer(
        job_id=uuid4(),
        base_model_id="meta-llama/Meta-Llama-3-8B",
        methodology="lora",
        training_config=LORA_CONFIG,
        dataset_rows=[ALPACA_ROW],
        output_dir=tmp_path,
        dataset_format="alpaca",
    )
    rows = trainer.prepare_dataset_rows()
    assert rows[0]["messages"][0]["role"] == "user"
    assert rows[0]["messages"][1]["role"] == "assistant"


def test_get_callbacks_returns_copy(tmp_path: Path) -> None:
    callback = MagicMock()
    trainer = DummyTrainer(
        job_id=uuid4(),
        base_model_id="meta-llama/Meta-Llama-3-8B",
        methodology="lora",
        training_config=LORA_CONFIG,
        dataset_rows=[ALPACA_ROW],
        output_dir=tmp_path,
        callbacks=[callback],
    )
    callbacks = trainer.get_callbacks()
    callbacks.append(MagicMock())
    assert trainer.get_callbacks() == [callback]


@patch("transformers.AutoModelForCausalLM")
@patch("transformers.AutoTokenizer")
def test_load_tokenizer_and_model_use_base_model_id(
    mock_tokenizer_cls: MagicMock,
    mock_model_cls: MagicMock,
    tmp_path: Path,
) -> None:
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token = None
    mock_tokenizer.eos_token = "<eos>"
    mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer
    mock_model_cls.from_pretrained.return_value = MagicMock()

    trainer = DummyTrainer(
        job_id=uuid4(),
        base_model_id="meta-llama/Meta-Llama-3-8B",
        methodology="lora",
        training_config=LORA_CONFIG,
        dataset_rows=[ALPACA_ROW],
        output_dir=tmp_path,
    )

    tokenizer = trainer.load_tokenizer()
    model = trainer.load_model()

    mock_tokenizer_cls.from_pretrained.assert_called_once_with(
        "meta-llama/Meta-Llama-3-8B",
        trust_remote_code=False,
    )
    mock_model_cls.from_pretrained.assert_called_once()
    assert mock_tokenizer.pad_token == "<eos>"
    assert tokenizer is mock_tokenizer
    assert model is mock_model_cls.from_pretrained.return_value


def test_train_returns_result_dict(tmp_path: Path) -> None:
    trainer = DummyTrainer(
        job_id=uuid4(),
        base_model_id="meta-llama/Meta-Llama-3-8B",
        methodology="lora",
        training_config=LORA_CONFIG,
        dataset_rows=[ALPACA_ROW],
        output_dir=tmp_path,
        dataset_format="unknown",
    )
    result = trainer.train()
    assert result["status"] == "completed"
    assert result["num_rows"] == 1
