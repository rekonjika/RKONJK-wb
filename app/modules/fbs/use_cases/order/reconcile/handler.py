# app/modules/fbs/use_cases/order/reconcile/handler.py

import logging
import time
from typing import Any
from sqlalchemy.orm import Session

from app.core.wb_client import WildberriesClient
from app.modules.fbs.domain.models.order import FbsOrder
from app.modules.fbs.domain.models.order_item import FbsOrderItem
from app.modules.fbs.domain.types.order_status import FbsOrderStatus
from app.modules.fbs.domain.types.wb_status import WbStatusResolver
from app.modules.inventory.domain.services.inventory_engine import InventoryEngine
from app.modules.fbs.use_cases.order.new.handler import NewOrderHandler

logger = logging.getLogger("reconcile_handler")


class ReconcileOrdersHandler:
    """Глубокая сверка статусов и отлов заказов из архива за последние N дней."""

    def __init__(self, db: Session, client: WildberriesClient) -> None:
        self.db = db
        self.client = client

    def handle(self, days_back: int = 14) -> int:
        recovered_count = self._catch_active_orders(days_back)
        self._reconcile_existing_statuses()
        return recovered_count

    def _catch_active_orders(self, days_back: int) -> int:
        raw_candidates = self._fetch_orders_archive(days_back)
        if not raw_candidates:
            return 0

        incoming_ids = [str(o["id"]) for o in raw_candidates if o.get("id")]
        existing_task_ids = {
            t_id for (t_id,) in self.db.query(FbsOrderItem.task_id).filter(FbsOrderItem.task_id.in_(incoming_ids)).all()
        }
        untracked = [o for o in raw_candidates if str(o.get("id")) not in existing_task_ids]
        if not untracked:
            return 0

        statuses_map = self._fetch_statuses_map([int(o["id"]) for o in untracked])
        really_active = []
        active_status_map: dict[int, str] = {}

        for o in untracked:
            t_id = int(o["id"])
            sup_st, wb_st = statuses_map.get(t_id, (None, None))
            if WbStatusResolver.is_cancelled(sup_st, wb_st) or wb_st == "sold":
                continue
            really_active.append(o)
            active_status_map[t_id] = sup_st or "new"

        if not really_active:
            return 0

        wh_map = {int(w["id"]): w.get("name", "Склад FBS") for w in self.client.get_warehouses()}
        return NewOrderHandler(self.db).handle(really_active, wh_map, status_map=active_status_map)

    def _fetch_orders_archive(self, days_back: int) -> list[dict[str, Any]]:
        date_from_ts = int(time.time()) - (days_back * 24 * 60 * 60)
        next_cursor = 0
        raw_candidates: list[dict[str, Any]] = []

        while True:
            data = self.client.get_orders_cursor(date_from_ts=date_from_ts, next_cursor=next_cursor, limit=1000)
            chunk = data.get("orders", [])
            raw_candidates.extend(chunk)
            next_val = data.get("next", 0)
            if not next_val or len(chunk) < 1000:
                break
            next_cursor = next_val

        return raw_candidates

    def _fetch_statuses_map(self, order_ids: list[int]) -> dict[int, tuple[str | None, str | None]]:
        statuses_map: dict[int, tuple[str | None, str | None]] = {}
        for i in range(0, len(order_ids), 200):
            chunk = order_ids[i:i + 200]
            try:
                for item in self.client.get_orders_statuses(chunk):
                    if item.get("id"):
                        statuses_map[int(item["id"])] = (item.get("supplierStatus"), item.get("wbStatus"))
            except Exception as exc:
                logger.error(f"[Recovery Status Error] {exc}")
        return statuses_map

    def _reconcile_existing_statuses(self) -> None:
        active_items = self.db.query(FbsOrderItem).join(FbsOrder).filter(
            FbsOrder.status.in_(FbsOrderStatus.active_statuses())
        ).all()
        task_map = {int(item.task_id): item for item in active_items if item.task_id and item.task_id.isdigit()}
        task_ids = list(task_map.keys())

        for i in range(0, len(task_ids), 200):
            chunk = task_ids[i:i + 200]
            statuses = self.client.get_orders_statuses(chunk)
            for st in statuses:
                item = task_map.get(st.get("id"))
                if not item or not item.order:
                    continue

                sup_st, wb_st = st.get("supplierStatus"), st.get("wbStatus")
                if WbStatusResolver.is_cancelled(sup_st, wb_st):
                    if item.order.status != FbsOrderStatus.CANCELLED.value:
                        if item.product_id:
                            InventoryEngine.release(self.db, item.product_id, quantity=1, task_id=item.task_id)
                        item.order.status = FbsOrderStatus.CANCELLED.value
                elif WbStatusResolver.is_completed(sup_st, wb_st):
                    item.order.status = FbsOrderStatus.COMPLETED.value

        self.db.commit()