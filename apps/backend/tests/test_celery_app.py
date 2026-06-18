from core.celery_app import celery
from core.config import settings


def test_celery_app_name() -> None:
    assert celery.main == "fts"


def test_celery_broker_and_backend_resolve_from_settings() -> None:
    assert celery.conf.broker_url == settings.CELERY_BROKER_URL
    assert celery.conf.result_backend == settings.CELERY_RESULT_BACKEND


def test_celery_serialization_defaults() -> None:
    assert celery.conf.task_serializer == "json"
    assert celery.conf.result_serializer == "json"
    assert celery.conf.accept_content == ["json"]
    assert celery.conf.timezone == "UTC"
    assert celery.conf.enable_utc is True


def test_celery_task_routes_map_training_and_export_queues() -> None:
    task_routes = celery.conf.task_routes
    assert task_routes["tasks.training_tasks.*"] == {"queue": "training"}
    assert task_routes["tasks.export_tasks.*"] == {"queue": "export"}
    assert celery.conf.task_default_queue == "default"
