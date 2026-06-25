from celery import Celery

from core.config import settings

celery = Celery(
    "fts",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_routes={
        "tasks.training_tasks.*": {"queue": "training"},
        "tasks.eval_tasks.*": {"queue": "training"},
        "tasks.export_tasks.*": {"queue": "export"},
    },
    task_default_queue="default",
)
