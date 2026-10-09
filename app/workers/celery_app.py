# app/workers/celery_app.py

from datetime import timedelta
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "rknjik_wb",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Moscow",
    enable_utc=True,
    task_track_started=True,
    result_expires=900,
    broker_pool_limit=10,
    redis_max_connections=20,
    task_ignore_result=True
)

celery_app.conf.beat_schedule = {
    "fbs-fast-orders-every-20s": {
        "task": "app.tasks.task_fbs_fast_orders_sync",
        "schedule": timedelta(seconds=20),
        "options": {"ignore_result": True}
    },
    "fbs-supplies-every-60s": {
        "task": "app.tasks.task_fbs_supplies_sync",
        "schedule": timedelta(seconds=60),
        "options": {"ignore_result": True}
    },
    "fbs-auto-push-stocks-every-2m": {
        "task": "app.tasks.task_fbs_auto_push_stocks",
        "schedule": timedelta(minutes=2),
        "options": {"ignore_result": True}
    },
    "fbs-reconcile-deep-every-15m": {
        "task": "app.tasks.task_fbs_reconcile_deep_sync",
        "schedule": timedelta(minutes=15),
        "options": {"ignore_result": True}
    },
}