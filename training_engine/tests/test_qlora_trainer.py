from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from trainers.base_trainer import TrainerError
from trainers.qlora_trainer import QLoRATrainer

ALPACA_ROW = {"instruction": "Summarize this.", "input": "Some text.", "output": "A summary."}

QLORA_CONFIG = {
    "learning_rate": 0.0002,
    "num_epochs": 1,
    "batch_size": 2,
    "max_seq_length": 512,
    "warmup_ratio": 0.03,
    "weight_decay": 0.0,
    "gradient_accumulation_steps": 1,
    "lora_r": 8,
    "lora_alpha": 16,
}


def _make_trainer(tmp_path: Path, **kwargs: Any) -> QLoRATrainer:
    defaults = {
        "job_id": uuid4(),
        "base_model_id": "meta-llama/Meta-Llama-3-8B",
        "methodology": "qlora",
        "training_config": QLORA_CONFIG,
        "dataset_rows": [ALPACA_ROW],
        "output_dir": tmp_path,
        "dataset_format": "alpaca",
    }
    defaults.update(kwargs)
    return QLoRATrainer(**defaults)


def test_qlora_trainer_rejects_non_qlora_methodology(tmp_path: Path) -> None:
    with pytest.raises(TrainerError, match="requires methodology='qlora'"):
        _make_trainer(tmp_path, methodology="lora")


def test_qlora_trainer_rejects_missing_lora_keys(tmp_path: Path) -> None:
    config = {
        "learning_rate": 0.0002,
        "num_epochs": 1,
        "batch_size": 2,
    }
    with pytest.raises(TrainerError, match="requires lora_r and lora_alpha"):
        _make_trainer(tmp_path, training_config=config)


@patch("trainers.lora_trainer.get_hf_dataset_class")
@patch("trainers.lora_trainer._get_trl_sft_trainer")
@patch("trainers.lora_trainer._get_peft_modules")
@patch("trainers.qlora_trainer._get_bitsandbytes_config_cls")
@patch("transformers.AutoModelForCausalLM")
@patch("transformers.AutoTokenizer")
def test_qlora_train_applies_bnb_peft_and_runs_trl_trainer(
    mock_tokenizer_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_get_bnb_cls: MagicMock,
    mock_get_peft: MagicMock,
    mock_get_trl: MagicMock,
    mock_dataset_cls: MagicMock,
    tmp_path: Path,
) -> None:
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token = None
    mock_tokenizer.eos_token = "<eos>"
    mock_tokenizer.apply_chat_template.return_value = "<chatml-formatted>"
    mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer

    mock_bnb_config_cls = MagicMock()
    mock_bnb_config = MagicMock()
    mock_bnb_config_cls.return_value = mock_bnb_config
    mock_get_bnb_cls.return_value = mock_bnb_config_cls

    mock_quantized_model = MagicMock()
    mock_model_cls.from_pretrained.return_value = mock_quantized_model

    mock_lora_config_cls = MagicMock()
    mock_lora_config = MagicMock()
    mock_lora_config_cls.return_value = mock_lora_config
    mock_get_peft_model = MagicMock()
    mock_peft_model = MagicMock()
    mock_get_peft_model.return_value = mock_peft_model
    mock_task_type = MagicMock()
    mock_task_type.CAUSAL_LM = "CAUSAL_LM"
    mock_get_peft.return_value = (mock_lora_config_cls, mock_get_peft_model, mock_task_type)

    mock_train_dataset = MagicMock()
    mock_dataset_cls.return_value.from_list.return_value = mock_train_dataset

    mock_trl_trainer_cls = MagicMock()
    mock_trl_instance = MagicMock()
    mock_trl_instance.train.return_value = MagicMock(metrics={"train_loss": 0.28})
    mock_trl_trainer_cls.return_value = mock_trl_instance
    mock_get_trl.return_value = mock_trl_trainer_cls

    trainer = _make_trainer(tmp_path)
    result = trainer.train()

    mock_bnb_config_cls.assert_called_once_with(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=mock_bnb_config_cls.call_args.kwargs["bnb_4bit_compute_dtype"],
        bnb_4bit_use_double_quant=True,
    )
    mock_model_cls.from_pretrained.assert_called_once_with(
        "meta-llama/Meta-Llama-3-8B",
        quantization_config=mock_bnb_config,
        device_map="auto",
        trust_remote_code=False,
    )

    mock_lora_config_cls.assert_called_once_with(
        r=8,
        lora_alpha=16,
        lora_dropout=0.05,
        target_modules=[
            "q_proj",
            "k_proj",
            "v_proj",
            "o_proj",
            "gate_proj",
            "up_proj",
            "down_proj",
        ],
        task_type="CAUSAL_LM",
    )
    mock_get_peft_model.assert_called_once_with(mock_quantized_model, mock_lora_config)

    mock_trl_trainer_cls.assert_called_once()
    trl_kwargs = mock_trl_trainer_cls.call_args.kwargs
    assert trl_kwargs["model"] is mock_peft_model
    assert trl_kwargs["tokenizer"] is mock_tokenizer
    assert trl_kwargs["train_dataset"] is mock_train_dataset
    assert trl_kwargs["max_seq_length"] == 512
    assert trl_kwargs["packing"] is False

    mock_trl_instance.train.assert_called_once()
    mock_trl_instance.save_model.assert_called_once_with(str(tmp_path / "final"))
    mock_tokenizer.save_pretrained.assert_called_once_with(str(tmp_path / "final"))

    assert result == {
        "status": "completed",
        "methodology": "qlora",
        "job_id": trainer.job_id,
        "output_dir": str(tmp_path),
        "model_dir": str(tmp_path / "final"),
        "num_rows": 1,
        "metrics": {"train_loss": 0.28},
    }


@patch("trainers.lora_trainer.get_hf_dataset_class")
@patch("trainers.lora_trainer._get_trl_sft_trainer")
@patch("trainers.lora_trainer._get_peft_modules")
@patch("trainers.qlora_trainer._get_bitsandbytes_config_cls")
@patch("transformers.AutoModelForCausalLM")
@patch("transformers.AutoTokenizer")
def test_qlora_train_passes_callbacks_to_trl_trainer(
    mock_tokenizer_cls: MagicMock,
    mock_model_cls: MagicMock,
    mock_get_bnb_cls: MagicMock,
    mock_get_peft: MagicMock,
    mock_get_trl: MagicMock,
    mock_dataset_cls: MagicMock,
    tmp_path: Path,
) -> None:
    callback = MagicMock()
    mock_tokenizer = MagicMock()
    mock_tokenizer.pad_token = "<pad>"
    mock_tokenizer.apply_chat_template.return_value = "text"
    mock_tokenizer_cls.from_pretrained.return_value = mock_tokenizer

    mock_bnb_config_cls = MagicMock()
    mock_get_bnb_cls.return_value = mock_bnb_config_cls
    mock_model_cls.from_pretrained.return_value = MagicMock()

    mock_lora_config_cls = MagicMock()
    mock_get_peft_model = MagicMock()
    mock_get_peft_model.return_value = MagicMock()
    mock_task_type = MagicMock()
    mock_task_type.CAUSAL_LM = "CAUSAL_LM"
    mock_get_peft.return_value = (mock_lora_config_cls, mock_get_peft_model, mock_task_type)

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
