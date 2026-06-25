from uuid import UUID

from core.exceptions import NotFoundError, ValidationError
from models.eval_job import EvalJob
from models.user import User
from schemas.eval import EvalBenchmarkCreate, EvalCompareCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tasks.eval_tasks import dispatch_eval_job

EVAL_STATUS_PENDING = "pending"

# Mirrors training_engine/evaluation/benchmark.py's BENCHMARK_TASKS keys -- duplicated
# here (same port-pattern as dataset_format.py/dataset_quality.py) so invalid benchmark
# names are rejected before a Celery round-trip, without importing training_engine.
SUPPORTED_BENCHMARKS = {"mmlu", "hellaswag", "arc"}


def _validate_benchmarks(benchmarks: list[str] | None) -> None:
    if not benchmarks:
        return
    unsupported = sorted(set(benchmarks) - SUPPORTED_BENCHMARKS)
    if unsupported:
        raise ValidationError(
            f"Unsupported benchmark(s): {unsupported}. Must be one of {sorted(SUPPORTED_BENCHMARKS)}."
        )


async def create_compare_job(payload: EvalCompareCreate, user: User, db: AsyncSession) -> EvalJob:
    _validate_benchmarks(payload.benchmarks)

    job = EvalJob(
        user_id=user.id,
        eval_type="compare",
        status=EVAL_STATUS_PENDING,
        base_model_id=payload.base_model_id,
        finetuned_model_id=payload.finetuned_model_id,
        prompts=payload.prompts,
        benchmarks=payload.benchmarks,
        num_fewshot=payload.num_fewshot,
        sample_limit=payload.sample_limit,
        max_new_tokens=payload.max_new_tokens,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    dispatch_eval_job.delay(
        eval_id=str(job.id),
        eval_type="compare",
        base_model_id=job.base_model_id,
        finetuned_model_id=job.finetuned_model_id,
        prompts=job.prompts,
        benchmarks=job.benchmarks,
        max_new_tokens=job.max_new_tokens,
        num_fewshot=job.num_fewshot,
        sample_limit=job.sample_limit,
    )

    return job


async def create_benchmark_job(
    payload: EvalBenchmarkCreate, user: User, db: AsyncSession
) -> EvalJob:
    _validate_benchmarks(payload.benchmarks)

    job = EvalJob(
        user_id=user.id,
        eval_type="benchmark",
        status=EVAL_STATUS_PENDING,
        base_model_id=payload.base_model_id,
        benchmarks=payload.benchmarks,
        num_fewshot=payload.num_fewshot,
        sample_limit=payload.sample_limit,
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    dispatch_eval_job.delay(
        eval_id=str(job.id),
        eval_type="benchmark",
        base_model_id=job.base_model_id,
        finetuned_model_id=None,
        prompts=None,
        benchmarks=job.benchmarks,
        max_new_tokens=None,
        num_fewshot=job.num_fewshot,
        sample_limit=job.sample_limit,
    )

    return job


async def list_eval_jobs(user: User, db: AsyncSession) -> list[EvalJob]:
    result = await db.scalars(
        select(EvalJob).where(EvalJob.user_id == user.id).order_by(EvalJob.created_at.desc())
    )
    return list(result)


async def get_eval_job(eval_id: UUID, user: User, db: AsyncSession) -> EvalJob:
    job = await db.scalar(select(EvalJob).where(EvalJob.id == eval_id, EvalJob.user_id == user.id))
    if job is None:
        raise NotFoundError("Evaluation job not found.")
    return job
