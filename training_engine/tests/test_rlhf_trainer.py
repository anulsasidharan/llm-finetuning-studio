from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from trainers.base_trainer import TrainerError
from trainers.rlhf_trainer import RLHFTrainer

PAIR_ROW = {
    "prompt": "What is the capital of France?",
    "chosen": "The capital of France is Paris.",
    "rejected": "I don't know.",
}

RLHF_CONFIG = {
    "learning_rate": 0.0002,
    "num_epochs": 1,
    "batch_size": 2,
    "max_seq_length": 512,
    "warmup_ratio": 0.03,
    "weight_decay": 0.0,
    "gradient_accumulation_steps": 1,
    "reward_model_id": "OpenAssistant/reward-model-deberta-v3-large-v2",
}


def _make_trainer(tmp_path: Path, **kwargs: Any) -> RLHFTrainer:
    defaults = {
        "job_id": uuid4(),
        "base_model_id": "meta-llama/Meta-Llama-3-8B",
        "methodology": "rlhf",
        "training_config": RLHF_CONFIG,
        "dataset_rows": [PAIR_ROW],
        "output_dir": tmp_path,
    }
    defaults.update(kwargs)
    return RLHFTrainer(**defaults)


def test_rlhf_trainer_rejects_non_rlhf_methodology(tmp_path: Path) -> None:
    with pytest.raises(TrainerError, match="requires methodology='rlhf'"):
        _make_trainer(tmp_path, methodology="dpo")


def test_rlhf_trainer_rejects_missing_reward_model_id(tmp_path: Path) -> None:
    config = {
        "learning_rate": 0.0002,
        "num_epochs": 1,
        "batch_size": 2,
    }
    with pytest.raises(TrainerError, match="requires reward_model_id"):
        _make_trainer(tmp_path, training_config=config)


def test_rlhf_trainer_rejects_row_missing_pair_keys(tmp_path: Path) -> None:
    trainer = _make_trainer(tmp_path, dataset_rows=[{"prompt": "hi", "chosen": "hello"}])
    with pytest.raises(TrainerError, match="missing required keys"):
        trainer.prepare_preference_rows()


def test_tokenize_reward_pairs_builds_chosen_and_rejected_ids(tmp_path: Path) -> None:
    tokenizer = MagicMock()
    tokenizer.side_effect = [
        {"input_ids": [1, 2], "attention_mask": [1, 1]},
        {"input_ids": [3, 4], "attention_mask": [1, 1]},
    ]
    trainer = _make_trainer(tmp_path)
    rows = trainer._tokenize_reward_pairs(tokenizer, [PAIR_ROW])

    assert len(rows) == 1
    assert rows[0]["input_ids_chosen"] == [1, 2]
    assert rows[0]["input_ids_rejected"] == [3, 4]
    assert tokenizer.call_count == 2


@patch("trainers.rlhf_trainer._get_trl_ppo_trainer")
@patch("trainers.rlhf_trainer._get_trl_value_head_model")
@patch("trainers.rlhf_trainer._get_trl_ppo_config")
@patch("trainers.rlhf_trainer.get_hf_dataset_class")
@patch("trainers.rlhf_trainer._get_trl_reward_trainer")
@patch("trainers.rlhf_trainer._get_trl_reward_config")
@patch("transformers.AutoModelForSequenceClassification")
@patch("transformers.AutoTokenizer")
def test_rlhf_train_runs_reward_then_ppo(
    mock_rm_tokenizer_cls: MagicMock,
    mock_rm_model_cls: MagicMock,
    mock_reward_config_cls: MagicMock,
    mock_get_reward_trainer: MagicMock,
    mock_dataset_cls: MagicMock,
    mock_ppo_config_cls: MagicMock,
    mock_value_head_cls: MagicMock,
    mock_get_ppo_trainer: MagicMock,
    tmp_path: Path,
) -> None:
    mock_rm_tokenizer = MagicMock()
    mock_rm_tokenizer.pad_token = None
    mock_rm_tokenizer.eos_token = "<eos>"
    mock_rm_tokenizer_cls.from_pretrained.return_value = mock_rm_tokenizer
    mock_rm_tokenizer.side_effect = [
        {"input_ids": [1], "attention_mask": [1]},
        {"input_ids": [2], "attention_mask": [1]},
    ]

    mock_rm_model = MagicMock()
    mock_rm_model.config.pad_token_id = None
    mock_rm_model.parameters.return_value = iter([MagicMock(device="cpu")])
    mock_rm_model.return_value.logits.squeeze.return_value = MagicMock(
        shape=(1,),
        detach=MagicMock(
            return_value=MagicMock(
                cpu=MagicMock(return_value=MagicMock(item=MagicMock(return_value=0.5)))
            )
        ),
    )
    mock_rm_model_cls.from_pretrained.return_value = mock_rm_model

    mock_reward_config_cls.return_value = MagicMock()
    mock_reward_trainer_cls = MagicMock()
    mock_reward_instance = MagicMock()
    mock_reward_instance.train.return_value = MagicMock(metrics={"train_loss": 0.11})
    mock_reward_trainer_cls.return_value = mock_reward_instance
    mock_get_reward_trainer.return_value = mock_reward_trainer_cls

    mock_dataset_cls.return_value.from_list.side_effect = [
        MagicMock(name="reward_dataset"),
        MagicMock(name="query_dataset", __len__=MagicMock(return_value=1)),
    ]

    mock_policy_tokenizer = MagicMock()
    mock_policy_tokenizer.pad_token = "<pad>"
    mock_policy_tokenizer.eos_token_id = 0
    mock_policy_tokenizer.encode.return_value = [10, 11]
    mock_policy_tokenizer.decode.return_value = "What is the capital of France?"
    mock_policy_tokenizer.batch_decode.return_value = ["Paris."]

    mock_ppo_config = MagicMock()
    mock_ppo_config.steps = 2
    mock_ppo_config_cls.return_value = MagicMock(return_value=mock_ppo_config)

    mock_policy_model = MagicMock()
    mock_ref_model = MagicMock()
    mock_value_head_cls.from_pretrained.side_effect = [mock_policy_model, mock_ref_model]

    mock_query_batch = {
        "input_ids": [MagicMock()],
        "query": ["What is the capital of France?"],
    }
    mock_ppo_instance = MagicMock()
    mock_ppo_instance.dataloader = [mock_query_batch]
    mock_ppo_instance.generate.return_value = [MagicMock()]
    mock_ppo_instance.step.return_value = {"ppo/mean_scores": 0.42}
    mock_ppo_trainer_cls = MagicMock(return_value=mock_ppo_instance)
    mock_get_ppo_trainer.return_value = mock_ppo_trainer_cls

    trainer = _make_trainer(tmp_path)
    with (
        patch.object(trainer, "load_tokenizer", return_value=mock_policy_tokenizer),
        patch.object(trainer, "_score_responses", return_value=[MagicMock()]),
    ):
        result = trainer.train()

    mock_reward_trainer_cls.assert_called_once()
    mock_ppo_trainer_cls.assert_called_once()
    mock_ppo_instance.generate.assert_called_once()
    mock_ppo_instance.step.assert_called_once()
    mock_ppo_instance.save_pretrained.assert_called_once_with(str(tmp_path / "final"))
    mock_reward_instance.save_model.assert_called_once_with(str(tmp_path / "reward_model"))

    assert result == {
        "status": "completed",
        "methodology": "rlhf",
        "job_id": trainer.job_id,
        "output_dir": str(tmp_path),
        "reward_model_dir": str(tmp_path / "reward_model"),
        "model_dir": str(tmp_path / "final"),
        "num_rows": 1,
        "metrics": {
            "train_loss": 0.11,
            "ppo_mean_reward": 0.42,
            "ppo_steps": 2,
        },
    }
