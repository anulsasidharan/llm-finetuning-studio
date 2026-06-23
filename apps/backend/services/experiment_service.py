from uuid import UUID

from core.exceptions import NotFoundError
from models.experiment import Experiment, ExperimentRun
from models.user import User
from schemas.experiment import ExperimentCreate, ExperimentRunCreate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.job_service import get_job

METRIC_FIELDS = (
    "train_loss",
    "eval_loss",
    "gpu_utilization_pct",
    "vram_used_gb",
    "tokens_per_second",
)


def _snapshot_job_metrics(job) -> dict[str, float | None]:
    return {field: getattr(job, field) for field in METRIC_FIELDS}


async def create_experiment(payload: ExperimentCreate, user: User, db: AsyncSession) -> Experiment:
    experiment = Experiment(
        user_id=user.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(experiment)
    await db.commit()
    await db.refresh(experiment)
    return experiment


async def list_experiments(user: User, db: AsyncSession) -> list[Experiment]:
    result = await db.scalars(
        select(Experiment)
        .where(Experiment.user_id == user.id)
        .order_by(Experiment.created_at.desc())
    )
    return list(result)


async def get_experiment(experiment_id: UUID, user: User, db: AsyncSession) -> Experiment:
    experiment = await db.scalar(
        select(Experiment).where(Experiment.id == experiment_id, Experiment.user_id == user.id)
    )
    if experiment is None:
        raise NotFoundError("Experiment not found.")
    return experiment


async def create_run(
    experiment_id: UUID, payload: ExperimentRunCreate, user: User, db: AsyncSession
) -> ExperimentRun:
    await get_experiment(experiment_id, user, db)
    job = await get_job(payload.fine_tune_job_id, user, db)

    run = ExperimentRun(
        experiment_id=experiment_id,
        fine_tune_job_id=job.id,
        metrics=_snapshot_job_metrics(job),
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)
    return run


async def compare_experiment(
    experiment_id: UUID, user: User, db: AsyncSession
) -> tuple[Experiment, list[ExperimentRun]]:
    experiment = await get_experiment(experiment_id, user, db)

    result = await db.scalars(
        select(ExperimentRun)
        .where(ExperimentRun.experiment_id == experiment_id)
        .options(selectinload(ExperimentRun.fine_tune_job))
        .order_by(ExperimentRun.created_at.asc())
    )
    runs = list(result)
    return experiment, runs


def build_metrics_by_name(runs: list[ExperimentRun]) -> dict[str, list[dict]]:
    metrics_by_name: dict[str, list[dict]] = {field: [] for field in METRIC_FIELDS}
    for run in runs:
        run_metrics = run.metrics or {}
        for field in METRIC_FIELDS:
            value = run_metrics.get(field)
            if value is not None:
                metrics_by_name[field].append({"run_id": str(run.id), "value": value})
    return metrics_by_name
