from uuid import UUID

from core.auth import get_current_user
from core.database import get_db
from fastapi import APIRouter, Depends
from models.experiment import Experiment, ExperimentRun
from models.user import User
from schemas.experiment import (
    ExperimentCompareResponse,
    ExperimentCreate,
    ExperimentResponse,
    ExperimentRunCompareEntry,
    ExperimentRunCreate,
    ExperimentRunResponse,
)
from services import experiment_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("", response_model=ExperimentResponse, status_code=201)
async def create_experiment(
    payload: ExperimentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    return await experiment_service.create_experiment(payload, current_user, db)


@router.get("", response_model=list[ExperimentResponse])
async def list_experiments(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Experiment]:
    return await experiment_service.list_experiments(current_user, db)


@router.get("/{experiment_id}", response_model=ExperimentResponse)
async def get_experiment(
    experiment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Experiment:
    return await experiment_service.get_experiment(experiment_id, current_user, db)


@router.post("/{experiment_id}/runs", response_model=ExperimentRunResponse, status_code=201)
async def create_run(
    experiment_id: UUID,
    payload: ExperimentRunCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExperimentRun:
    return await experiment_service.create_run(experiment_id, payload, current_user, db)


@router.get("/{experiment_id}/compare", response_model=ExperimentCompareResponse)
async def compare_experiment(
    experiment_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ExperimentCompareResponse:
    experiment, runs = await experiment_service.compare_experiment(experiment_id, current_user, db)
    return ExperimentCompareResponse(
        experiment_id=experiment.id,
        runs=[
            ExperimentRunCompareEntry(
                run_id=run.id,
                fine_tune_job_id=run.fine_tune_job_id,
                base_model_id=run.fine_tune_job.base_model_id,
                methodology=run.fine_tune_job.methodology,
                status=run.fine_tune_job.status,
                training_config=run.fine_tune_job.training_config,
                metrics=run.metrics,
                created_at=run.created_at,
            )
            for run in runs
        ],
        metrics_by_name=experiment_service.build_metrics_by_name(runs),
    )
