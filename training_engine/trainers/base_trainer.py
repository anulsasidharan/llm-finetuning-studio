"""Abstract base trainer for all fine-tuning methodologies."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal
from uuid import UUID

import structlog
from datasets.formatter import to_chatml
from transformers import PreTrainedModel, PreTrainedTokenizerBase, TrainingArguments

logger = structlog.get_logger()

Methodology = Literal["sft", "lora", "qlora", "dpo", "orpo", "rlhf"]
SUPPORTED_METHODOLOGIES: frozenset[str] = frozenset({"sft", "lora", "qlora", "dpo", "orpo", "rlhf"})


class TrainerError(ValueError):
    """Raised when trainer inputs or setup are invalid."""


@dataclass(frozen=True)
class TrainerConfig:
    """Normalized view of the flat ``training_config`` dict stored on ``FineTuneJob``."""

    learning_rate: float
    num_epochs: int
    batch_size: int
    warmup_ratio: float = 0.03
    weight_decay: float = 0.0
    max_seq_length: int = 2048
    gradient_accumulation_steps: int = 1
    lora_r: int | None = None
    lora_alpha: int | None = None
    beta: float | None = None
    reward_model_id: str | None = None

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> TrainerConfig:
        missing = {"learning_rate", "num_epochs", "batch_size"} - raw.keys()
        if missing:
            raise TrainerError(f"training_config is missing required keys: {sorted(missing)}")

        return cls(
            learning_rate=float(raw["learning_rate"]),
            num_epochs=int(raw["num_epochs"]),
            batch_size=int(raw["batch_size"]),
            warmup_ratio=float(raw.get("warmup_ratio", 0.03)),
            weight_decay=float(raw.get("weight_decay", 0.0)),
            max_seq_length=int(raw.get("max_seq_length", 2048)),
            gradient_accumulation_steps=int(raw.get("gradient_accumulation_steps", 1)),
            lora_r=int(raw["lora_r"]) if raw.get("lora_r") is not None else None,
            lora_alpha=int(raw["lora_alpha"]) if raw.get("lora_alpha") is not None else None,
            beta=float(raw["beta"]) if raw.get("beta") is not None else None,
            reward_model_id=str(raw["reward_model_id"]) if raw.get("reward_model_id") else None,
        )


class BaseTrainer(ABC):
    """Shared setup for methodology-specific trainers.

    Accepts the same flat ``training_config`` dict the backend persists today.
    Dataset rows are passed in pre-loaded by the Celery caller — no HF
    ``datasets`` import here (avoids the local-package naming collision).
    Quantization and PEFT wiring are left to subclasses (e.g. QLoRA in
    ``qlora_trainer.py``).
    """

    def __init__(
        self,
        *,
        job_id: UUID | str,
        base_model_id: str,
        methodology: str,
        training_config: dict[str, Any],
        dataset_rows: list[dict[str, Any]],
        output_dir: str | Path,
        dataset_format: str = "chatml",
        callbacks: list[Any] | None = None,
        trust_remote_code: bool = False,
    ) -> None:
        if methodology not in SUPPORTED_METHODOLOGIES:
            raise TrainerError(
                f"Unsupported methodology: {methodology}. "
                f"Must be one of {sorted(SUPPORTED_METHODOLOGIES)}."
            )
        if not dataset_rows:
            raise TrainerError("dataset_rows must contain at least one example.")

        self.job_id = str(job_id)
        self.base_model_id = base_model_id
        self.methodology = methodology
        self.config = TrainerConfig.from_dict(training_config)
        self.dataset_rows = dataset_rows
        self.output_dir = Path(output_dir)
        self.dataset_format = dataset_format
        self.trust_remote_code = trust_remote_code
        self._callbacks: list[Any] = list(callbacks or [])

        self.output_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "trainer_initialized",
            job_id=self.job_id,
            base_model_id=self.base_model_id,
            methodology=self.methodology,
            num_rows=len(self.dataset_rows),
            output_dir=str(self.output_dir),
        )

    def resolve_device(self) -> str:
        import torch

        if torch.cuda.is_available():
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def load_tokenizer(self) -> PreTrainedTokenizerBase:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            self.base_model_id,
            trust_remote_code=self.trust_remote_code,
        )
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        return tokenizer

    def load_model(self) -> PreTrainedModel:
        """Load the base causal LM. Subclasses override for quantization / PEFT."""
        import torch
        from transformers import AutoModelForCausalLM

        device = self.resolve_device()
        dtype = torch.float16 if device == "cuda" else torch.float32
        return AutoModelForCausalLM.from_pretrained(
            self.base_model_id,
            torch_dtype=dtype,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=self.trust_remote_code,
        )

    def build_training_arguments(self) -> TrainingArguments:
        return TrainingArguments(
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
        )

    def prepare_dataset_rows(self) -> list[dict[str, Any]]:
        """Normalize raw rows to canonical ChatML ``{"messages": [...]}``."""
        format_hint = None if self.dataset_format == "unknown" else self.dataset_format
        return [to_chatml(row, format=format_hint) for row in self.dataset_rows]

    def get_callbacks(self) -> list[Any]:
        """Return trainer callbacks.

        Stays caller-injected (PHASE2-007 decision): the Celery training task
        constructs ``utils.callbacks.MetricsCallback(job_id=...)`` itself and
        passes it via the ``callbacks=`` constructor kwarg, same as every
        other external dependency (``dataset_rows``, etc.) is threaded in.
        """
        return list(self._callbacks)

    @abstractmethod
    def train(self) -> dict[str, Any]:
        """Run training and return final metrics / artifact metadata."""
