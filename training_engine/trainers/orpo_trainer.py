"""ORPO trainer — single-pass SFT + preference alignment via ``trl.ORPOTrainer``."""

from __future__ import annotations

from typing import Any

import structlog
from utils.hf_datasets import ensure_hf_datasets_loaded, get_hf_dataset_class

from trainers.base_trainer import BaseTrainer, TrainerError

logger = structlog.get_logger()

REQUIRED_PAIR_KEYS = ("prompt", "chosen", "rejected")


def _get_trl_orpo_trainer() -> type:
    ensure_hf_datasets_loaded()
    from trl import ORPOTrainer as TrlORPOTrainer

    return TrlORPOTrainer


def _get_trl_orpo_config() -> type:
    ensure_hf_datasets_loaded()
    from trl import ORPOConfig as TrlORPOConfig

    return TrlORPOConfig


class ORPOTrainer(BaseTrainer):
    """Run ORPO odds-ratio preference alignment — no frozen reference model."""

    def __init__(self, *, methodology: str = "orpo", **kwargs: Any) -> None:
        if methodology != "orpo":
            raise TrainerError(f"ORPOTrainer requires methodology='orpo', got {methodology!r}.")
        super().__init__(methodology=methodology, **kwargs)
        if self.config.beta is None:
            raise TrainerError("ORPO training requires beta in training_config.")

    def _validate_pair_row(self, row: dict[str, Any]) -> dict[str, Any]:
        missing = [key for key in REQUIRED_PAIR_KEYS if key not in row]
        if missing:
            raise TrainerError(
                f"ORPO dataset row is missing required keys {missing}: keys={sorted(row.keys())}"
            )
        return {key: row[key] for key in REQUIRED_PAIR_KEYS}

    def prepare_preference_rows(self) -> list[dict[str, Any]]:
        """Validate raw rows already carry ``prompt``/``chosen``/``rejected`` keys.

        Same preference-pair shape as DPO — ``BaseTrainer.prepare_dataset_rows``/
        ``to_chatml`` don't apply.
        """
        return [self._validate_pair_row(row) for row in self.dataset_rows]

    def _build_train_dataset(self, rows: list[dict[str, Any]]):
        dataset_cls = get_hf_dataset_class()
        return dataset_cls.from_list(rows)

    def _build_orpo_args(self):
        """ORPO's beta/max_length/max_prompt_length live on the args object, not
        as direct ``ORPOTrainer`` constructor kwargs (unlike DPOTrainer's beta=)."""
        TrlORPOConfig = _get_trl_orpo_config()
        return TrlORPOConfig(
            output_dir=str(self.output_dir),
            num_train_epochs=self.config.num_epochs,
            per_device_train_batch_size=self.config.batch_size,
            learning_rate=self.config.learning_rate,
            warmup_ratio=self.config.warmup_ratio,
            weight_decay=self.config.weight_decay,
            gradient_accumulation_steps=self.config.gradient_accumulation_steps,
            logging_steps=10,
            save_strategy="epoch",
            report_to="none",
            remove_unused_columns=False,
            beta=self.config.beta,
            max_length=self.config.max_seq_length,
            max_prompt_length=self.config.max_seq_length // 2,
        )

    def train(self) -> dict[str, Any]:
        TrlORPOTrainer = _get_trl_orpo_trainer()

        tokenizer = self.load_tokenizer()
        model = self.load_model()
        orpo_args = self._build_orpo_args()
        pair_rows = self.prepare_preference_rows()
        train_dataset = self._build_train_dataset(pair_rows)
        callbacks = self.get_callbacks()
        model_dir = self.output_dir / "final"

        logger.info(
            "orpo_training_start",
            job_id=self.job_id,
            base_model_id=self.base_model_id,
            beta=self.config.beta,
            num_rows=len(pair_rows),
            max_seq_length=self.config.max_seq_length,
        )

        orpo_trainer = TrlORPOTrainer(
            model=model,
            args=orpo_args,
            train_dataset=train_dataset,
            tokenizer=tokenizer,
            callbacks=callbacks,
        )

        train_result = orpo_trainer.train()
        metrics = dict(train_result.metrics) if train_result.metrics else {}

        orpo_trainer.save_model(str(model_dir))
        tokenizer.save_pretrained(str(model_dir))

        logger.info(
            "orpo_training_completed",
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
            "num_rows": len(pair_rows),
            "metrics": metrics,
        }
