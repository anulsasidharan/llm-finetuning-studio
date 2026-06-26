"""RLHF trainer — reward-model fine-tuning then PPO policy optimisation.

Phase 1 uses ``trl.RewardTrainer`` on preference pairs (``prompt``/``chosen``/
``rejected``) starting from ``training_config.reward_model_id``.
Phase 2 uses ``trl.PPOTrainer`` with the fine-tuned reward model scoring
policy generations from ``base_model_id``.
"""

from __future__ import annotations

from typing import Any

import structlog
from utils.hf_datasets import ensure_hf_datasets_loaded, get_hf_dataset_class

from trainers.base_trainer import BaseTrainer, TrainerError

logger = structlog.get_logger()

REQUIRED_PAIR_KEYS = ("prompt", "chosen", "rejected")
DEFAULT_PPO_MAX_NEW_TOKENS = 64


def _get_trl_reward_trainer() -> type:
    ensure_hf_datasets_loaded()
    from trl import RewardTrainer as TrlRewardTrainer

    return TrlRewardTrainer


def _get_trl_reward_config() -> type:
    ensure_hf_datasets_loaded()
    from trl import RewardConfig as TrlRewardConfig

    return TrlRewardConfig


def _get_trl_ppo_trainer() -> type:
    ensure_hf_datasets_loaded()
    from trl import PPOTrainer as TrlPPOTrainer

    return TrlPPOTrainer


def _get_trl_ppo_config() -> type:
    ensure_hf_datasets_loaded()
    from trl import PPOConfig as TrlPPOConfig

    return TrlPPOConfig


def _get_trl_value_head_model() -> type:
    ensure_hf_datasets_loaded()
    from trl import AutoModelForCausalLMWithValueHead

    return AutoModelForCausalLMWithValueHead


def _ppo_collator(data: list[dict[str, Any]]) -> dict[str, list[Any]]:
    return {key: [row[key] for row in data] for key in data[0]}


class RLHFTrainer(BaseTrainer):
    """Two-phase RLHF: train a reward model, then optimise the policy with PPO."""

    def __init__(self, *, methodology: str = "rlhf", **kwargs: Any) -> None:
        if methodology != "rlhf":
            raise TrainerError(f"RLHFTrainer requires methodology='rlhf', got {methodology!r}.")
        super().__init__(methodology=methodology, **kwargs)
        if not self.config.reward_model_id:
            raise TrainerError("RLHF training requires reward_model_id in training_config.")

    def _validate_pair_row(self, row: dict[str, Any]) -> dict[str, Any]:
        missing = [key for key in REQUIRED_PAIR_KEYS if key not in row]
        if missing:
            raise TrainerError(
                f"RLHF dataset row is missing required keys {missing}: keys={sorted(row.keys())}"
            )
        return {key: row[key] for key in REQUIRED_PAIR_KEYS}

    def prepare_preference_rows(self) -> list[dict[str, Any]]:
        """Validate raw rows carry ``prompt``/``chosen``/``rejected`` keys."""
        return [self._validate_pair_row(row) for row in self.dataset_rows]

    def _build_reward_args(self, reward_output_dir: str):
        TrlRewardConfig = _get_trl_reward_config()
        return TrlRewardConfig(
            output_dir=reward_output_dir,
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
            max_length=self.config.max_seq_length,
        )

    def _tokenize_reward_pairs(
        self,
        tokenizer: Any,
        pair_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        tokenized_rows: list[dict[str, Any]] = []
        for row in pair_rows:
            chosen_text = f"{row['prompt']}{row['chosen']}"
            rejected_text = f"{row['prompt']}{row['rejected']}"
            tokenized_chosen = tokenizer(
                chosen_text,
                truncation=True,
                max_length=self.config.max_seq_length,
            )
            tokenized_rejected = tokenizer(
                rejected_text,
                truncation=True,
                max_length=self.config.max_seq_length,
            )
            tokenized_rows.append(
                {
                    "input_ids_chosen": tokenized_chosen["input_ids"],
                    "attention_mask_chosen": tokenized_chosen["attention_mask"],
                    "input_ids_rejected": tokenized_rejected["input_ids"],
                    "attention_mask_rejected": tokenized_rejected["attention_mask"],
                }
            )
        return tokenized_rows

    def _train_reward_model(
        self,
        pair_rows: list[dict[str, Any]],
        reward_dir: str,
        callbacks: list[Any],
    ) -> tuple[Any, Any, dict[str, Any]]:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        TrlRewardTrainer = _get_trl_reward_trainer()
        reward_args = self._build_reward_args(reward_dir)

        reward_tokenizer = AutoTokenizer.from_pretrained(
            self.config.reward_model_id,
            trust_remote_code=self.trust_remote_code,
        )
        if reward_tokenizer.pad_token is None:
            reward_tokenizer.pad_token = reward_tokenizer.eos_token

        device = self.resolve_device()
        dtype = torch.float16 if device == "cuda" else torch.float32
        reward_model = AutoModelForSequenceClassification.from_pretrained(
            self.config.reward_model_id,
            num_labels=1,
            torch_dtype=dtype,
            device_map="auto" if device == "cuda" else None,
            trust_remote_code=self.trust_remote_code,
        )
        if reward_model.config.pad_token_id is None:
            reward_model.config.pad_token_id = reward_tokenizer.pad_token_id

        tokenized_rows = self._tokenize_reward_pairs(reward_tokenizer, pair_rows)
        dataset_cls = get_hf_dataset_class()
        train_dataset = dataset_cls.from_list(tokenized_rows)

        logger.info(
            "rlhf_reward_training_start",
            job_id=self.job_id,
            reward_model_id=self.config.reward_model_id,
            num_rows=len(pair_rows),
        )

        reward_trainer = TrlRewardTrainer(
            model=reward_model,
            args=reward_args,
            train_dataset=train_dataset,
            tokenizer=reward_tokenizer,
            callbacks=callbacks,
        )
        train_result = reward_trainer.train()
        metrics = dict(train_result.metrics) if train_result.metrics else {}

        reward_trainer.save_model(reward_dir)
        reward_tokenizer.save_pretrained(reward_dir)

        logger.info(
            "rlhf_reward_training_completed",
            job_id=self.job_id,
            reward_dir=reward_dir,
            train_loss=metrics.get("train_loss"),
        )
        return reward_model, reward_tokenizer, metrics

    def _build_ppo_config(self, num_prompts: int):
        TrlPPOConfig = _get_trl_ppo_config()
        batch_size = max(1, self.config.batch_size)
        mini_batch_size = max(1, min(batch_size, batch_size))
        grad_accum = max(1, self.config.gradient_accumulation_steps)
        backward_batch = mini_batch_size * grad_accum
        if batch_size % backward_batch != 0:
            batch_size = backward_batch

        steps_per_epoch = max(1, (num_prompts + batch_size - 1) // batch_size)
        steps = max(batch_size, self.config.num_epochs * steps_per_epoch)

        return TrlPPOConfig(
            learning_rate=self.config.learning_rate,
            batch_size=batch_size,
            mini_batch_size=mini_batch_size,
            gradient_accumulation_steps=grad_accum,
            steps=steps,
            remove_unused_columns=False,
        )

    def _build_query_dataset(self, tokenizer: Any, pair_rows: list[dict[str, Any]]):
        max_query_length = max(8, self.config.max_seq_length // 2)
        query_rows: list[dict[str, Any]] = []
        for row in pair_rows:
            input_ids = tokenizer.encode(
                row["prompt"],
                truncation=True,
                max_length=max_query_length,
            )
            if not input_ids:
                continue
            query_rows.append(
                {
                    "input_ids": input_ids,
                    "query": tokenizer.decode(input_ids, skip_special_tokens=True),
                }
            )

        if not query_rows:
            raise TrainerError("RLHF PPO phase has no valid prompts after tokenization.")

        dataset_cls = get_hf_dataset_class()
        dataset = dataset_cls.from_list(query_rows)
        dataset.set_format(type="torch")
        return dataset

    def _score_responses(
        self,
        reward_model: Any,
        reward_tokenizer: Any,
        queries: list[str],
        responses: list[str],
    ) -> list[Any]:
        import torch

        device = next(reward_model.parameters()).device
        texts = [f"{query}{response}" for query, response in zip(queries, responses, strict=True)]
        inputs = reward_tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.config.max_seq_length,
        )
        inputs = {key: value.to(device) for key, value in inputs.items()}
        with torch.no_grad():
            logits = reward_model(**inputs).logits.squeeze(-1)
        return [logits[i].detach().cpu() for i in range(logits.shape[0])]

    def _run_ppo(
        self,
        pair_rows: list[dict[str, Any]],
        reward_model: Any,
        reward_tokenizer: Any,
    ) -> dict[str, Any]:
        TrlPPOTrainer = _get_trl_ppo_trainer()
        AutoModelForCausalLMWithValueHead = _get_trl_value_head_model()

        policy_tokenizer = self.load_tokenizer()
        query_dataset = self._build_query_dataset(policy_tokenizer, pair_rows)
        ppo_config = self._build_ppo_config(len(query_dataset))

        policy_model = AutoModelForCausalLMWithValueHead.from_pretrained(
            self.base_model_id,
            trust_remote_code=self.trust_remote_code,
        )
        ref_model = AutoModelForCausalLMWithValueHead.from_pretrained(
            self.base_model_id,
            trust_remote_code=self.trust_remote_code,
        )

        ppo_trainer = TrlPPOTrainer(
            ppo_config,
            policy_model,
            ref_model,
            policy_tokenizer,
            dataset=query_dataset,
            data_collator=_ppo_collator,
        )

        generation_kwargs = {
            "min_length": -1,
            "top_k": 0.0,
            "top_p": 1.0,
            "do_sample": True,
            "pad_token_id": policy_tokenizer.eos_token_id,
            "max_new_tokens": DEFAULT_PPO_MAX_NEW_TOKENS,
        }

        logger.info(
            "rlhf_ppo_training_start",
            job_id=self.job_id,
            base_model_id=self.base_model_id,
            ppo_steps=ppo_config.steps,
            num_queries=len(query_dataset),
        )

        last_stats: dict[str, Any] = {}
        for batch in ppo_trainer.dataloader:
            query_tensors = batch["input_ids"]
            response_tensors = ppo_trainer.generate(
                query_tensors,
                return_prompt=False,
                **generation_kwargs,
            )
            query_texts = batch["query"]
            response_texts = policy_tokenizer.batch_decode(
                response_tensors,
                skip_special_tokens=True,
            )
            rewards = self._score_responses(
                reward_model,
                reward_tokenizer,
                query_texts,
                response_texts,
            )
            last_stats = ppo_trainer.step(query_tensors, response_tensors, rewards)

        model_dir = self.output_dir / "final"
        ppo_trainer.save_pretrained(str(model_dir))
        policy_tokenizer.save_pretrained(str(model_dir))

        logger.info(
            "rlhf_ppo_training_completed",
            job_id=self.job_id,
            output_dir=str(self.output_dir),
            mean_reward=last_stats.get("ppo/mean_scores"),
        )

        return {
            "ppo_steps": ppo_config.steps,
            "mean_reward": last_stats.get("ppo/mean_scores"),
            "stats": last_stats,
        }

    def train(self) -> dict[str, Any]:
        pair_rows = self.prepare_preference_rows()
        callbacks = self.get_callbacks()
        reward_dir = str(self.output_dir / "reward_model")

        reward_model, reward_tokenizer, reward_phase_metrics = self._train_reward_model(
            pair_rows, reward_dir, callbacks
        )
        ppo_metrics = self._run_ppo(pair_rows, reward_model, reward_tokenizer)
        model_dir = self.output_dir / "final"

        combined_metrics = {
            **reward_phase_metrics,
            "ppo_mean_reward": ppo_metrics.get("mean_reward"),
            "ppo_steps": ppo_metrics.get("ppo_steps"),
        }

        return {
            "status": "completed",
            "methodology": self.methodology,
            "job_id": self.job_id,
            "output_dir": str(self.output_dir),
            "reward_model_dir": reward_dir,
            "model_dir": str(model_dir),
            "num_rows": len(pair_rows),
            "metrics": combined_metrics,
        }
