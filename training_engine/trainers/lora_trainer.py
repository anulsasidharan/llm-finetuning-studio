"""LoRA trainer — low-rank adapters on a frozen base via ``peft`` + ``trl.SFTTrainer``."""

from __future__ import annotations

from typing import Any

import structlog
from transformers import PreTrainedModel, PreTrainedTokenizerBase
from utils.hf_datasets import ensure_hf_datasets_loaded, get_hf_dataset_class

from trainers.base_trainer import BaseTrainer, TrainerError

logger = structlog.get_logger()

DEFAULT_LORA_TARGET_MODULES: tuple[str, ...] = (
    "q_proj",
    "k_proj",
    "v_proj",
    "o_proj",
    "gate_proj",
    "up_proj",
    "down_proj",
)
DEFAULT_LORA_DROPOUT = 0.05


def _get_peft_modules() -> tuple[type, Any, Any]:
    from peft import LoraConfig, TaskType, get_peft_model

    return LoraConfig, get_peft_model, TaskType


def _get_trl_sft_trainer() -> type:
    ensure_hf_datasets_loaded()
    from trl import SFTTrainer as TrlSFTTrainer

    return TrlSFTTrainer


class LoRATrainer(BaseTrainer):
    """Run supervised fine-tuning with LoRA adapters on a frozen base model."""

    def __init__(self, *, methodology: str = "lora", **kwargs: Any) -> None:
        if methodology != "lora":
            raise TrainerError(f"LoRATrainer requires methodology='lora', got {methodology!r}.")
        super().__init__(methodology=methodology, **kwargs)
        if self.config.lora_r is None or self.config.lora_alpha is None:
            raise TrainerError("LoRA training requires lora_r and lora_alpha in training_config.")

    def _build_lora_config(self) -> Any:
        LoraConfig, _, TaskType = _get_peft_modules()
        return LoraConfig(
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=DEFAULT_LORA_DROPOUT,
            target_modules=list(DEFAULT_LORA_TARGET_MODULES),
            task_type=TaskType.CAUSAL_LM,
        )

    def _apply_lora(self, model: PreTrainedModel) -> PreTrainedModel:
        _, get_peft_model, _ = _get_peft_modules()
        return get_peft_model(model, self._build_lora_config())

    def _format_chatml_example(
        self,
        example: dict[str, Any],
        tokenizer: PreTrainedTokenizerBase,
    ) -> str:
        return tokenizer.apply_chat_template(
            example["messages"],
            tokenize=False,
            add_generation_prompt=False,
        )

    def _build_train_dataset(self, rows: list[dict[str, Any]]):
        dataset_cls = get_hf_dataset_class()
        return dataset_cls.from_list(rows)

    def train(self) -> dict[str, Any]:
        TrlSFTTrainer = _get_trl_sft_trainer()

        tokenizer = self.load_tokenizer()
        base_model = self.load_model()
        model = self._apply_lora(base_model)
        training_args = self.build_training_arguments()
        chatml_rows = self.prepare_dataset_rows()
        train_dataset = self._build_train_dataset(chatml_rows)
        callbacks = self.get_callbacks()
        model_dir = self.output_dir / "final"

        logger.info(
            "lora_training_start",
            job_id=self.job_id,
            base_model_id=self.base_model_id,
            lora_r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            num_rows=len(chatml_rows),
            max_seq_length=self.config.max_seq_length,
        )

        sft_trainer = TrlSFTTrainer(
            model=model,
            args=training_args,
            train_dataset=train_dataset,
            tokenizer=tokenizer,
            formatting_func=lambda example: self._format_chatml_example(example, tokenizer),
            max_seq_length=self.config.max_seq_length,
            callbacks=callbacks,
            packing=False,
        )

        train_result = sft_trainer.train()
        metrics = dict(train_result.metrics) if train_result.metrics else {}

        sft_trainer.save_model(str(model_dir))
        tokenizer.save_pretrained(str(model_dir))

        logger.info(
            "lora_training_completed",
            job_id=self.job_id,
            output_dir=str(self.output_dir),
            train_loss=metrics.get("train_loss"),
        )

        return {
            "status": "completed",
            "methodology": self.methodology,
            "job_id": self.job_id,
            "output_dir": str(self.output_dir),
            "model_dir": str(model_dir),
            "num_rows": len(chatml_rows),
            "metrics": metrics,
        }
