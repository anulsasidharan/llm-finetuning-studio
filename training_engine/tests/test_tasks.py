import json
from unittest.mock import MagicMock, patch

import tasks
from trainers.base_trainer import TrainerError

VALID_KWARGS = dict(
    job_id="job-1",
    base_model_id="meta-llama/Meta-Llama-3-8B",
    methodology="sft",
    training_config={"learning_rate": 0.0001, "num_epochs": 1, "batch_size": 2},
    dataset_storage_path="user/file.json",
    dataset_format="chatml",
)


def _run(**overrides):
    kwargs = {**VALID_KWARGS, **overrides}
    return tasks.run_training_job.run(**kwargs)


def test_run_training_job_rejects_rlhf_methodology() -> None:
    with (
        patch("tasks.mark_job_failed") as mock_failed,
        patch("tasks.download_dataset_file") as mock_download,
    ):
        result = _run(methodology="rlhf")

    assert result["status"] == "failed"
    assert "rlhf" in result["error"]
    mock_failed.assert_called_once()
    mock_download.assert_not_called()


def test_run_training_job_marks_failed_on_dataset_load_error() -> None:
    with (
        patch("tasks.download_dataset_file", side_effect=RuntimeError("minio down")),
        patch("tasks.mark_job_failed") as mock_failed,
    ):
        result = _run()

    assert result["status"] == "failed"
    assert "minio down" in result["error"]
    mock_failed.assert_called_once()


def test_run_training_job_marks_failed_on_empty_dataset() -> None:
    with (
        patch("tasks.download_dataset_file", return_value=b"[]"),
        patch("tasks.mark_job_failed") as mock_failed,
    ):
        result = _run()

    assert result["status"] == "failed"
    assert result["error"] == "Dataset has no rows."
    mock_failed.assert_called_once_with("job-1", "Dataset has no rows.")


def test_run_training_job_happy_path_constructs_trainer_and_marks_completed() -> None:
    fake_trainer_instance = MagicMock()
    fake_trainer_instance.train.return_value = {
        "status": "completed",
        "metrics": {"train_loss": 0.5, "eval_loss": 0.4},
    }
    fake_trainer_cls = MagicMock(return_value=fake_trainer_instance)
    dataset_bytes = json.dumps([{"messages": [{"role": "user", "content": "hi"}]}]).encode()

    with (
        patch.dict(tasks.TRAINER_CLASSES, {"sft": fake_trainer_cls}),
        patch("tasks.download_dataset_file", return_value=dataset_bytes),
        patch("tasks.mark_job_running") as mock_running,
        patch("tasks.mark_job_completed") as mock_completed,
        patch("tasks.GPUMonitor") as mock_gpu_monitor_cls,
        patch("tasks.MetricsCallback") as mock_metrics_cb,
        patch("tasks.MetricsPersistCallback") as mock_persist_cb,
    ):
        mock_gpu_monitor_cls.return_value.sample = MagicMock()
        result = _run()

    mock_running.assert_called_once_with("job-1")
    fake_trainer_cls.assert_called_once()
    call_kwargs = fake_trainer_cls.call_args.kwargs
    assert call_kwargs["job_id"] == "job-1"
    assert call_kwargs["base_model_id"] == "meta-llama/Meta-Llama-3-8B"
    assert call_kwargs["methodology"] == "sft"
    assert call_kwargs["dataset_rows"] == [{"messages": [{"role": "user", "content": "hi"}]}]
    assert call_kwargs["dataset_format"] == "chatml"
    assert len(call_kwargs["callbacks"]) == 2
    mock_metrics_cb.assert_called_once()
    mock_persist_cb.assert_called_once()
    fake_trainer_instance.train.assert_called_once()
    mock_completed.assert_called_once_with("job-1", train_loss=0.5, eval_loss=0.4)
    assert result["status"] == "completed"


def test_run_training_job_catches_trainer_error() -> None:
    fake_trainer_cls = MagicMock(side_effect=TrainerError("bad config"))
    dataset_bytes = json.dumps([{"messages": []}]).encode()

    with (
        patch.dict(tasks.TRAINER_CLASSES, {"sft": fake_trainer_cls}),
        patch("tasks.download_dataset_file", return_value=dataset_bytes),
        patch("tasks.mark_job_running"),
        patch("tasks.mark_job_failed") as mock_failed,
        patch("tasks.GPUMonitor"),
        patch("tasks.MetricsCallback"),
        patch("tasks.MetricsPersistCallback"),
    ):
        result = _run()

    assert result["status"] == "failed"
    assert result["error"] == "bad config"
    mock_failed.assert_called_once_with("job-1", "bad config")


def test_run_training_job_catches_unexpected_training_exception() -> None:
    fake_trainer_instance = MagicMock()
    fake_trainer_instance.train.side_effect = RuntimeError("CUDA OOM")
    fake_trainer_cls = MagicMock(return_value=fake_trainer_instance)
    dataset_bytes = json.dumps([{"messages": []}]).encode()

    with (
        patch.dict(tasks.TRAINER_CLASSES, {"sft": fake_trainer_cls}),
        patch("tasks.download_dataset_file", return_value=dataset_bytes),
        patch("tasks.mark_job_running"),
        patch("tasks.mark_job_failed") as mock_failed,
        patch("tasks.GPUMonitor"),
        patch("tasks.MetricsCallback"),
        patch("tasks.MetricsPersistCallback"),
    ):
        result = _run()

    assert result["status"] == "failed"
    assert "CUDA OOM" in result["error"]
    mock_failed.assert_called_once()


def _run_eval(**overrides):
    kwargs = {
        "eval_id": "eval-1",
        "eval_type": "compare",
        "base_model_id": "gpt2",
        "finetuned_model_id": "gpt2-ft",
        "prompts": ["hello"],
        **overrides,
    }
    return tasks.run_eval_job.run(**kwargs)


def test_run_eval_job_compare_happy_path() -> None:
    fake_result = {"status": "completed", "completions": [{"prompt": "hello"}]}
    with (
        patch("tasks.mark_eval_running") as mock_running,
        patch("tasks.compare_models", return_value=fake_result) as mock_compare,
        patch("tasks.mark_eval_completed") as mock_completed,
    ):
        result = _run_eval()

    mock_running.assert_called_once_with("eval-1")
    mock_compare.assert_called_once_with(
        prompts=["hello"],
        base_model_id="gpt2",
        finetuned_model_id="gpt2-ft",
        benchmarks=None,
        max_new_tokens=256,
        num_fewshot=None,
        limit=None,
    )
    mock_completed.assert_called_once_with("eval-1", fake_result)
    assert result == fake_result


def test_run_eval_job_benchmark_happy_path() -> None:
    fake_result = {"status": "completed", "metrics": {"mmlu": {}}}
    with (
        patch("tasks.mark_eval_running"),
        patch("tasks.run_benchmark", return_value=fake_result) as mock_benchmark,
        patch("tasks.mark_eval_completed") as mock_completed,
    ):
        result = _run_eval(
            eval_type="benchmark",
            finetuned_model_id=None,
            prompts=None,
            benchmarks=["mmlu"],
        )

    mock_benchmark.assert_called_once_with(
        benchmarks=["mmlu"], model_id="gpt2", num_fewshot=None, limit=None
    )
    mock_completed.assert_called_once_with("eval-1", fake_result)
    assert result == fake_result


def test_run_eval_job_rejects_unsupported_eval_type() -> None:
    with (
        patch("tasks.mark_eval_running"),
        patch("tasks.mark_eval_failed") as mock_failed,
    ):
        result = _run_eval(eval_type="unknown")

    assert result["status"] == "failed"
    assert "unknown" in result["error"]
    mock_failed.assert_called_once()


def test_run_eval_job_catches_exception_from_compare() -> None:
    with (
        patch("tasks.mark_eval_running"),
        patch("tasks.compare_models", side_effect=RuntimeError("model not found")),
        patch("tasks.mark_eval_failed") as mock_failed,
    ):
        result = _run_eval()

    assert result["status"] == "failed"
    assert "model not found" in result["error"]
    mock_failed.assert_called_once_with("eval-1", "model not found")
