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
        "tasks.notification_tasks.*": {"queue": "default"},
    },
    task_default_queue="default",
)

# Register task modules with the worker process (celery -A core.celery_app worker).
import tasks.eval_tasks as _eval_tasks  # noqa: E402, F401
import tasks.export_tasks as _export_tasks  # noqa: E402, F401
import tasks.notification_tasks as _notification_tasks  # noqa: E402, F401
import tasks.training_tasks as _training_tasks  # noqa: E402, F401
