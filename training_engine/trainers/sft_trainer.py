"""Supervised fine-tuning trainer — full weight updates via ``trl.SFTTrainer``."""

from __future__ import annotations

from typing import Any

import structlog
from transformers import PreTrainedTokenizerBase
from utils.hf_datasets import ensure_hf_datasets_loaded, get_hf_dataset_class

from trainers.base_trainer import BaseTrainer, TrainerError

logger = structlog.get_logger()


def _get_trl_sft_trainer() -> type:
    ensure_hf_datasets_loaded()
    from trl import SFTTrainer as TrlSFTTrainer

    return TrlSFTTrainer


class SFTTrainer(BaseTrainer):
    """Run full supervised fine-tuning on the base model (no PEFT)."""

    def __init__(self, *, methodology: str = "sft", **kwargs: Any) -> None:
        if methodology != "sft":
            raise TrainerError(f"SFTTrainer requires methodology='sft', got {methodology!r}.")
        super().__init__(methodology=methodology, **kwargs)

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
        model = self.load_model()
        training_args = self.build_training_arguments()
        chatml_rows = self.prepare_dataset_rows()
        train_dataset = self._build_train_dataset(chatml_rows)
        callbacks = self.get_callbacks()
        model_dir = self.output_dir / "final"

        logger.info(
            "sft_training_start",
            job_id=self.job_id,
            base_model_id=self.base_model_id,
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
            "sft_training_completed",
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
