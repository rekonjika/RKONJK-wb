# app/modules/fbs/messenger/fbs_tasks.py

import logging
from functools import wraps
from typing import Any, Callable
import redis

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.wb_client import WildberriesClient
from app.workers.celery_app import celery_app
from app.modules.fbs.use_cases.order.new.handler import NewOrderHandler
from app.modules.fbs.use_cases.order.reconcile.handler import ReconcileOrdersHandler
from app.modules.fbs.use_cases.supply.sync.handler import SyncSuppliesHandler
from app.modules.fbs.use_cases.stock.push_delta.handler import PushDeltaStocksHandler

logger = logging.getLogger("fbs_messenger")


def fbs_task_lock(lock_name: str, timeout: int = 180) -> Callable[..., Any]:
    """Распределенный лок Redis против гонок данных при параллельном выполнении."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            client = redis.Redis.from_url(settings.REDIS_URL)
            lock = client.lock(f"rknjik:fbs_lock:{lock_name}", timeout=timeout)
            try:
                acquired = lock.acquire(blocking=False)
            except redis.RedisError as exc:
                logger.error(f"[Lock Error] {lock_name}: {exc}")
                return {"status": "skipped", "reason": "lock_unavailable"}

            if not acquired:
                logger.info(f"[Lock Skip] Задача {lock_name} уже выполняется в другом воркере.")
                return {"status": "skipped", "reason": "already_running"}

            try:
                return func(*args, **kwargs)
            finally:
                try:
                    lock.release()
                except redis.RedisError:
                    pass

        return wrapped
    return decorator


@celery_app.task(name="app.tasks.task_fbs_fast_orders_sync")
@fbs_task_lock("fast-orders", timeout=30)
def task_fbs_fast_orders_sync() -> dict[str, Any]:
    """Быстрый забор новых заказов (20 сек) + дельта-пуш остатков при изменениях."""
    if not settings.WB_API_KEY:
        return {"status": "skipped", "reason": "WB_API_KEY missing"}

    with SessionLocal() as db:
        client = WildberriesClient(settings.WB_API_KEY)
        raw_orders = client.get_new_orders()
        wh_map = {int(w["id"]): w.get("name", "Склад FBS") for w in client.get_warehouses()}

        new_count = NewOrderHandler(db).handle(raw_orders, wh_map)
        stocks_updated = 0
        if new_count > 0:
            stocks_updated = PushDeltaStocksHandler(db, client).handle()

        return {"status": "success", "new_orders": new_count, "stocks_updated": stocks_updated}


@celery_app.task(name="app.tasks.task_fbs_auto_push_stocks")
@fbs_task_lock("auto-push-stocks", timeout=120)
def task_fbs_auto_push_stocks() -> dict[str, Any]:
    """Регулярный дельта-пуш остатков на витрину WB (2 минуты)."""
    if not settings.WB_API_KEY:
        return {"status": "skipped", "reason": "WB_API_KEY missing"}

    with SessionLocal() as db:
        client = WildberriesClient(settings.WB_API_KEY)
        count = PushDeltaStocksHandler(db, client).handle()
        return {"status": "success", "stocks_updated": count}


@celery_app.task(name="app.tasks.task_fbs_supplies_sync")
@fbs_task_lock("supplies-sync", timeout=60)
def task_fbs_supplies_sync() -> dict[str, Any]:
    """Синхронизация поставок и их состава через order-ids (60 секунд)."""
    if not settings.WB_API_KEY:
        return {"status": "skipped", "reason": "WB_API_KEY missing"}

    with SessionLocal() as db:
        client = WildberriesClient(settings.WB_API_KEY)
        count = SyncSuppliesHandler(db, client).handle()
        return {"status": "success", "synced_supplies": count}


@celery_app.task(
    name="app.tasks.task_fbs_reconcile_deep_sync",
    time_limit=600,
    soft_time_limit=540
)
@fbs_task_lock("reconcile", timeout=600)
def task_fbs_reconcile_deep_sync() -> dict[str, Any]:
    """Глубокая сверка статусов, карусель и отлов отмен (15 минут)."""
    if not settings.WB_API_KEY:
        return {"status": "skipped", "reason": "WB_API_KEY missing"}

    with SessionLocal() as db:
        client = WildberriesClient(settings.WB_API_KEY)
        count = ReconcileOrdersHandler(db, client).handle(days_back=7)
        return {"status": "success", "recovered_orders": count}