from unittest.mock import MagicMock, patch

import pytest
from evaluation.benchmark import BenchmarkError, run_benchmark


def _patch_lm_eval(raw_results: dict) -> tuple:
    mock_lm_eval = MagicMock()
    mock_lm_eval.simple_evaluate.return_value = raw_results
    mock_hflm_cls = MagicMock()
    return (
        patch("evaluation.benchmark._get_lm_eval", return_value=mock_lm_eval),
        patch("evaluation.benchmark._get_hflm_cls", return_value=mock_hflm_cls),
        mock_lm_eval,
        mock_hflm_cls,
    )


def test_run_benchmark_rejects_empty_benchmarks_list() -> None:
    with pytest.raises(BenchmarkError, match="at least one benchmark"):
        run_benchmark(benchmarks=[], model_id="gpt2")


def test_run_benchmark_rejects_unsupported_benchmark() -> None:
    with pytest.raises(BenchmarkError, match="Unsupported benchmark"):
        run_benchmark(benchmarks=["truthful_qa"], model_id="gpt2")


def test_run_benchmark_rejects_neither_model_id_nor_loaded_model() -> None:
    with pytest.raises(BenchmarkError, match="Provide either model_id"):
        run_benchmark(benchmarks=["mmlu"])


def test_run_benchmark_rejects_both_model_id_and_loaded_model() -> None:
    with pytest.raises(BenchmarkError, match="Provide either model_id"):
        run_benchmark(
            benchmarks=["mmlu"],
            model_id="gpt2",
            model=MagicMock(),
            tokenizer=MagicMock(),
        )


def test_run_benchmark_with_model_id_constructs_hflm_from_pretrained_string() -> None:
    raw_results = {"results": {"hellaswag": {"acc,none": 0.6, "acc_stderr,none": 0.01}}}
    patch_lm_eval, patch_hflm, mock_lm_eval, mock_hflm_cls = _patch_lm_eval(raw_results)

    with patch_lm_eval, patch_hflm:
        result = run_benchmark(benchmarks=["hellaswag"], model_id="gpt2", device="cpu")

    mock_hflm_cls.assert_called_once_with(
        pretrained="gpt2",
        device="cpu",
        batch_size=8,
        trust_remote_code=False,
    )
    mock_lm_eval.simple_evaluate.assert_called_once()
    call_kwargs = mock_lm_eval.simple_evaluate.call_args.kwargs
    assert call_kwargs["tasks"] == ["hellaswag"]
    assert call_kwargs["device"] == "cpu"

    assert result == {
        "status": "completed",
        "model_id": "gpt2",
        "benchmarks": ["hellaswag"],
        "metrics": {"hellaswag": {"acc,none": 0.6, "acc_stderr,none": 0.01}},
    }


def test_run_benchmark_with_loaded_model_passes_model_and_tokenizer_to_hflm() -> None:
    raw_results = {"results": {"mmlu": {"acc,none": 0.42}}}
    patch_lm_eval, patch_hflm, mock_lm_eval, mock_hflm_cls = _patch_lm_eval(raw_results)

    fake_model = MagicMock()
    fake_tokenizer = MagicMock()

    with patch_lm_eval, patch_hflm:
        result = run_benchmark(
            benchmarks=["mmlu"],
            model=fake_model,
            tokenizer=fake_tokenizer,
            device="cpu",
        )

    mock_hflm_cls.assert_called_once_with(
        pretrained=fake_model,
        tokenizer=fake_tokenizer,
        batch_size=8,
    )
    assert result["model_id"] is None
    assert result["metrics"] == {"mmlu": {"acc,none": 0.42}}


def test_run_benchmark_arc_expands_to_easy_and_challenge_tasks() -> None:
    raw_results = {
        "results": {
            "arc_easy": {"acc,none": 0.7},
            "arc_challenge": {"acc,none": 0.5},
        }
    }
    patch_lm_eval, patch_hflm, mock_lm_eval, _ = _patch_lm_eval(raw_results)

    with patch_lm_eval, patch_hflm:
        result = run_benchmark(benchmarks=["arc"], model_id="gpt2", device="cpu")

    call_kwargs = mock_lm_eval.simple_evaluate.call_args.kwargs
    assert call_kwargs["tasks"] == ["arc_easy", "arc_challenge"]
    assert result["metrics"] == {
        "arc": {
            "arc_easy": {"acc,none": 0.7},
            "arc_challenge": {"acc,none": 0.5},
        }
    }


def test_run_benchmark_passes_num_fewshot_and_limit_through() -> None:
    raw_results = {"results": {"mmlu": {}}}
    patch_lm_eval, patch_hflm, mock_lm_eval, _ = _patch_lm_eval(raw_results)

    with patch_lm_eval, patch_hflm:
        run_benchmark(benchmarks=["mmlu"], model_id="gpt2", device="cpu", num_fewshot=5, limit=10)

    call_kwargs = mock_lm_eval.simple_evaluate.call_args.kwargs
    assert call_kwargs["num_fewshot"] == 5
    assert call_kwargs["limit"] == 10


def test_run_benchmark_defaults_to_resolved_device_when_not_given() -> None:
    raw_results = {"results": {"mmlu": {}}}
    patch_lm_eval, patch_hflm, mock_lm_eval, mock_hflm_cls = _patch_lm_eval(raw_results)

    with (
        patch_lm_eval,
        patch_hflm,
        patch("evaluation.benchmark._resolve_device", return_value="cuda"),
    ):
        run_benchmark(benchmarks=["mmlu"], model_id="gpt2")

    mock_hflm_cls.assert_called_once_with(
        pretrained="gpt2",
        device="cuda",
        batch_size=8,
        trust_remote_code=False,
    )


def test_run_benchmark_missing_task_in_results_defaults_to_empty_dict() -> None:
    raw_results = {"results": {}}
    patch_lm_eval, patch_hflm, _, _ = _patch_lm_eval(raw_results)

    with patch_lm_eval, patch_hflm:
        result = run_benchmark(benchmarks=["hellaswag"], model_id="gpt2", device="cpu")

    assert result["metrics"] == {"hellaswag": {}}
