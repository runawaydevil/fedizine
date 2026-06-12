from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "fedizine",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone=settings.default_timezone,
    enable_utc=True,
    beat_schedule={
        "collect-all-sources-daily": {
            "task": "app.workers.tasks.collect_all_users",
            "schedule": crontab(hour=6, minute=0),
        },
    },
)
