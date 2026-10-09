# app/workers/tasks.py

# Реэкспорт задач в единый реестр Celery
from app.modules.fbs.messenger.fbs_tasks import (
    task_fbs_fast_orders_sync,
    task_fbs_auto_push_stocks,
    task_fbs_supplies_sync,
    task_fbs_reconcile_deep_sync
)

__all__ = [
    "task_fbs_fast_orders_sync",
    "task_fbs_auto_push_stocks",
    "task_fbs_supplies_sync",
    "task_fbs_reconcile_deep_sync"
]