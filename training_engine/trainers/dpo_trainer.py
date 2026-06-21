"""DPO trainer — preference alignment on chosen/rejected pairs via ``trl.DPOTrainer``."""

from __future__ import annotations

from typing import Any

import structlog
from utils.hf_datasets import ensure_hf_datasets_loaded, get_hf_dataset_class

from trainers.base_trainer import BaseTrainer, TrainerError

logger = structlog.get_logger()

REQUIRED_PAIR_KEYS = ("prompt", "chosen", "rejected")


def _get_trl_dpo_trainer() -> type:
    ensure_hf_datasets_loaded()
    from trl import DPOTrainer as TrlDPOTrainer

    return TrlDPOTrainer


class DPOTrainer(BaseTrainer):
    """Run DPO preference alignment against a frozen reference model copy."""

    def __init__(self, *, methodology: str = "dpo", **kwargs: Any) -> None:
        if methodology != "dpo":
            raise TrainerError(f"DPOTrainer requires methodology='dpo', got {methodology!r}.")
        super().__init__(methodology=methodology, **kwargs)
        if self.config.beta is None:
            raise TrainerError("DPO training requires beta in training_config.")

    def _validate_pair_row(self, row: dict[str, Any]) -> dict[str, Any]:
        missing = [key for key in REQUIRED_PAIR_KEYS if key not in row]
        if missing:
            raise TrainerError(
                f"DPO dataset row is missing required keys {missing}: keys={sorted(row.keys())}"
            )
        return {key: row[key] for key in REQUIRED_PAIR_KEYS}

    def prepare_preference_rows(self) -> list[dict[str, Any]]:
        """Validate raw rows already carry ``prompt``/``chosen``/``rejected`` keys.

        Unlike SFT/LoRA/QLoRA, DPO rows are preference pairs, not ChatML
        messages — ``BaseTrainer.prepare_dataset_rows``/``to_chatml`` don't apply.
        """
        return [self._validate_pair_row(row) for row in self.dataset_rows]

    def _build_train_dataset(self, rows: list[dict[str, Any]]):
        dataset_cls = get_hf_dataset_class()
        return dataset_cls.from_list(rows)

    def train(self) -> dict[str, Any]:
        TrlDPOTrainer = _get_trl_dpo_trainer()

        tokenizer = self.load_tokenizer()
        model = self.load_model()
        ref_model = self.load_model()
        training_args = self.build_training_arguments()
        pair_rows = self.prepare_preference_rows()
        train_dataset = self._build_train_dataset(pair_rows)
        callbacks = self.get_callbacks()
        model_dir = self.output_dir / "final"
        max_prompt_length = self.config.max_seq_length // 2

        logger.info(
            "dpo_training_start",
            job_id=self.job_id,
            base_model_id=self.base_model_id,
            beta=self.config.beta,
            num_rows=len(pair_rows),
            max_seq_length=self.config.max_seq_length,
        )

        dpo_trainer = TrlDPOTrainer(
            model=model,
            ref_model=ref_model,
            beta=self.config.beta,
            args=training_args,
            train_dataset=train_dataset,
            tokenizer=tokenizer,
            max_length=self.config.max_seq_length,
            max_prompt_length=max_prompt_length,
            callbacks=callbacks,
        )

        train_result = dpo_trainer.train()
        metrics = dict(train_result.metrics) if train_result.metrics else {}

        dpo_trainer.save_model(str(model_dir))
        tokenizer.save_pretrained(str(model_dir))

        logger.info(
            "dpo_training_completed",
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
