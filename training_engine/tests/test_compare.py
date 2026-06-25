from unittest.mock import MagicMock

import pytest
from evaluation.compare import CompareError, compare_models


def _patch_loading(monkeypatch, *, base_model_id="base") -> tuple[MagicMock, MagicMock]:
    """Patch model loading + generation so no real torch/transformers work happens."""
    mock_model = MagicMock(name="model")
    mock_tokenizer = MagicMock(name="tokenizer")
    monkeypatch.setattr(
        "evaluation.compare._load_model_and_tokenizer",
        MagicMock(return_value=(mock_model, mock_tokenizer)),
    )
    monkeypatch.setattr(
        "evaluation.compare._generate",
        MagicMock(side_effect=lambda model, tokenizer, prompt, **kwargs: f"reply-to:{prompt}"),
    )
    return mock_model, mock_tokenizer


def test_compare_models_rejects_empty_prompts() -> None:
    with pytest.raises(CompareError, match="at least one prompt"):
        compare_models(prompts=[], base_model_id="gpt2", finetuned_model_id="gpt2-ft")


def test_compare_models_rejects_neither_base_model_id_nor_loaded_model(monkeypatch) -> None:
    _patch_loading(monkeypatch)
    with pytest.raises(CompareError, match="Provide either base_model_id"):
        compare_models(prompts=["hi"], finetuned_model_id="gpt2-ft")


def test_compare_models_rejects_both_base_model_id_and_loaded_model(monkeypatch) -> None:
    _patch_loading(monkeypatch)
    with pytest.raises(CompareError, match="Provide either base_model_id"):
        compare_models(
            prompts=["hi"],
            base_model_id="gpt2",
            base_model=MagicMock(),
            base_tokenizer=MagicMock(),
            finetuned_model_id="gpt2-ft",
        )


def test_compare_models_rejects_neither_finetuned_model_id_nor_loaded_model(monkeypatch) -> None:
    _patch_loading(monkeypatch)
    with pytest.raises(CompareError, match="Provide either finetuned_model_id"):
        compare_models(prompts=["hi"], base_model_id="gpt2")


def test_compare_models_with_model_ids_loads_both_sides_and_generates_completions(
    monkeypatch,
) -> None:
    mock_load = MagicMock(return_value=(MagicMock(), MagicMock()))
    monkeypatch.setattr("evaluation.compare._load_model_and_tokenizer", mock_load)
    monkeypatch.setattr(
        "evaluation.compare._generate",
        MagicMock(side_effect=lambda model, tokenizer, prompt, **kwargs: f"reply-to:{prompt}"),
    )

    result = compare_models(
        prompts=["What is LoRA?"],
        base_model_id="gpt2",
        finetuned_model_id="gpt2-ft",
        device="cpu",
    )

    assert mock_load.call_count == 2
    mock_load.assert_any_call("gpt2", device="cpu", trust_remote_code=False)
    mock_load.assert_any_call("gpt2-ft", device="cpu", trust_remote_code=False)
    assert result["status"] == "completed"
    assert result["base_model_id"] == "gpt2"
    assert result["finetuned_model_id"] == "gpt2-ft"
    assert result["completions"] == [
        {
            "prompt": "What is LoRA?",
            "base_completion": "reply-to:What is LoRA?",
            "finetuned_completion": "reply-to:What is LoRA?",
        }
    ]
    assert "benchmarks" not in result


def test_compare_models_with_loaded_models_skips_loading(monkeypatch) -> None:
    mock_load = MagicMock()
    monkeypatch.setattr("evaluation.compare._load_model_and_tokenizer", mock_load)
    monkeypatch.setattr(
        "evaluation.compare._generate",
        MagicMock(side_effect=lambda model, tokenizer, prompt, **kwargs: "ok"),
    )

    result = compare_models(
        prompts=["hi"],
        base_model=MagicMock(),
        base_tokenizer=MagicMock(),
        finetuned_model=MagicMock(),
        finetuned_tokenizer=MagicMock(),
        device="cpu",
    )

    mock_load.assert_not_called()
    assert result["base_model_id"] is None
    assert result["finetuned_model_id"] is None


def test_compare_models_includes_benchmark_delta_when_benchmarks_given(monkeypatch) -> None:
    base_model, base_tokenizer = MagicMock(), MagicMock()
    finetuned_model, finetuned_tokenizer = MagicMock(), MagicMock()
    monkeypatch.setattr(
        "evaluation.compare._generate",
        MagicMock(side_effect=lambda model, tokenizer, prompt, **kwargs: "ok"),
    )

    base_result = {"metrics": {"mmlu": {"acc,none": 0.4}}}
    finetuned_result = {"metrics": {"mmlu": {"acc,none": 0.55}}}
    mock_run_benchmark = MagicMock(side_effect=[base_result, finetuned_result])
    monkeypatch.setattr("evaluation.compare.run_benchmark", mock_run_benchmark)

    result = compare_models(
        prompts=["hi"],
        base_model=base_model,
        base_tokenizer=base_tokenizer,
        finetuned_model=finetuned_model,
        finetuned_tokenizer=finetuned_tokenizer,
        benchmarks=["mmlu"],
        device="cpu",
    )

    assert mock_run_benchmark.call_count == 2
    first_call_kwargs = mock_run_benchmark.call_args_list[0].kwargs
    assert first_call_kwargs["model"] is base_model
    assert first_call_kwargs["tokenizer"] is base_tokenizer
    second_call_kwargs = mock_run_benchmark.call_args_list[1].kwargs
    assert second_call_kwargs["model"] is finetuned_model
    assert second_call_kwargs["tokenizer"] is finetuned_tokenizer

    assert result["benchmarks"] == {
        "base": {"mmlu": {"acc,none": 0.4}},
        "finetuned": {"mmlu": {"acc,none": 0.55}},
        "delta": {"mmlu": {"acc,none": pytest.approx(0.15)}},
    }


def test_compare_models_omits_benchmarks_key_when_not_requested(monkeypatch) -> None:
    monkeypatch.setattr(
        "evaluation.compare._generate",
        MagicMock(side_effect=lambda model, tokenizer, prompt, **kwargs: "ok"),
    )
    mock_run_benchmark = MagicMock()
    monkeypatch.setattr("evaluation.compare.run_benchmark", mock_run_benchmark)

    result = compare_models(
        prompts=["hi"],
        base_model=MagicMock(),
        base_tokenizer=MagicMock(),
        finetuned_model=MagicMock(),
        finetuned_tokenizer=MagicMock(),
        device="cpu",
    )

    mock_run_benchmark.assert_not_called()
    assert "benchmarks" not in result


def test_compare_models_defaults_to_resolved_device_when_not_given(monkeypatch) -> None:
    mock_load = MagicMock(return_value=(MagicMock(), MagicMock()))
    monkeypatch.setattr("evaluation.compare._load_model_and_tokenizer", mock_load)
    monkeypatch.setattr(
        "evaluation.compare._generate",
        MagicMock(side_effect=lambda model, tokenizer, prompt, **kwargs: "ok"),
    )
    monkeypatch.setattr("evaluation.compare._resolve_device", MagicMock(return_value="cuda"))

    compare_models(prompts=["hi"], base_model_id="gpt2", finetuned_model_id="gpt2-ft")

    mock_load.assert_any_call("gpt2", device="cuda", trust_remote_code=False)
    mock_load.assert_any_call("gpt2-ft", device="cuda", trust_remote_code=False)


def test_diff_metrics_handles_nested_arc_style_dicts() -> None:
    from evaluation.compare import _diff_metrics

    base = {"arc": {"arc_easy": {"acc,none": 0.7}, "arc_challenge": {"acc,none": 0.5}}}
    finetuned = {"arc": {"arc_easy": {"acc,none": 0.75}, "arc_challenge": {"acc,none": 0.52}}}

    diff = _diff_metrics(base, finetuned)

    assert diff["arc"]["arc_easy"]["acc,none"] == pytest.approx(0.05)
    assert diff["arc"]["arc_challenge"]["acc,none"] == pytest.approx(0.02)
