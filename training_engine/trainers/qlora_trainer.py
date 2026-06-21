"""QLoRA trainer — 4-bit NF4 quantization + LoRA adapters via ``bitsandbytes`` + ``peft``."""

from __future__ import annotations

from typing import Any

import structlog
from transformers import PreTrainedModel

from trainers.base_trainer import BaseTrainer, TrainerError
from trainers.lora_trainer import LoRATrainer

logger = structlog.get_logger()


def _get_bitsandbytes_config_cls() -> type:
    from transformers import BitsAndBytesConfig

    return BitsAndBytesConfig


class QLoRATrainer(LoRATrainer):
    """Run supervised fine-tuning with 4-bit NF4 QLoRA on a frozen quantized base."""

    def __init__(self, *, methodology: str = "qlora", **kwargs: Any) -> None:
        if methodology != "qlora":
            raise TrainerError(f"QLoRATrainer requires methodology='qlora', got {methodology!r}.")
        BaseTrainer.__init__(self, methodology=methodology, **kwargs)
        if self.config.lora_r is None or self.config.lora_alpha is None:
            raise TrainerError("QLoRA training requires lora_r and lora_alpha in training_config.")

    def _build_bnb_config(self) -> Any:
        import torch

        BitsAndBytesConfig = _get_bitsandbytes_config_cls()
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )

    def load_model(self) -> PreTrainedModel:
        from transformers import AutoModelForCausalLM

        bnb_config = self._build_bnb_config()
        logger.info(
            "qlora_loading_quantized_base",
            job_id=self.job_id,
            base_model_id=self.base_model_id,
            quant_type="nf4",
        )
        return AutoModelForCausalLM.from_pretrained(
            self.base_model_id,
            quantization_config=bnb_config,
            device_map="auto",
            trust_remote_code=self.trust_remote_code,
        )
