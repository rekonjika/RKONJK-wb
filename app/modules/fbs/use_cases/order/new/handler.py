# app/modules/fbs/use_cases/order/new/handler.py

import logging
from datetime import datetime, timedelta
from typing import Any
from sqlalchemy.orm import Session

from app.modules.catalog.domain.models.product import Product
from app.modules.fbs.domain.models.order import FbsOrder
from app.modules.fbs.domain.models.order_item import FbsOrderItem
from app.modules.fbs.domain.types.order_status import FbsOrderStatus
from app.modules.inventory.domain.services.inventory_engine import InventoryEngine

logger = logging.getLogger("new_order_handler")


class NewOrderHandler:
    """Регистрирует новые задания, связывает с Product и ставит бронь в WMS."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def handle(
        self,
        raw_orders: list[dict[str, Any]],
        wh_map: dict[int, str],
        status_map: dict[int, str] | None = None
    ) -> int:
        if not raw_orders:
            return 0

        existing_task_ids, existing_orders = self._load_existing_metadata(raw_orders)
        products_map = self._load_products_map(raw_orders)
        created_count = 0

        for task in raw_orders:
            task_id = str(task.get("id"))
            if task_id in existing_task_ids:
                continue

            order_uid = str(task.get("orderUid"))
            db_order = existing_orders.get(order_uid) or self._create_order_header(task, wh_map, status_map)
            existing_orders[order_uid] = db_order

            self._create_order_item(task, db_order.id, products_map)
            existing_task_ids.add(task_id)
            created_count += 1

            if created_count % 500 == 0:
                self.db.commit()

        if created_count > 0:
            self.db.commit()

        return created_count

    def _load_existing_metadata(self, raw_orders: list[dict[str, Any]]) -> tuple[set[str], dict[str, FbsOrder]]:
        t_ids = [str(t.get("id")) for t in raw_orders if t.get("id")]
        uids = [str(t.get("orderUid")) for t in raw_orders if t.get("orderUid")]

        existing_task_ids = {
            tid for (tid,) in self.db.query(FbsOrderItem.task_id).filter(FbsOrderItem.task_id.in_(t_ids)).all()
        }
        existing_orders = {
            o.order_uid: o for o in self.db.query(FbsOrder).filter(FbsOrder.order_uid.in_(uids)).all()
        }
        return existing_task_ids, existing_orders

    def _load_products_map(self, raw_orders: list[dict[str, Any]]) -> dict[str, Product]:
        barcodes = {str(t.get("skus", [""])[0]).strip() for t in raw_orders if t.get("skus")}
        if not barcodes:
            return {}
        products = self.db.query(Product).filter(Product.barcode.in_(list(barcodes))).all()
        return {str(p.barcode).strip(): p for p in products if p.barcode}

    def _create_order_header(
        self,
        task: dict[str, Any],
        wh_map: dict[int, str],
        status_map: dict[int, str] | None
    ) -> FbsOrder:
        wh_id = int(task["warehouseId"]) if task.get("warehouseId") else None
        wh_name = wh_map.get(wh_id, "Склад FBS") if wh_id else "Склад FBS"
        raw_status = (status_map.get(int(task["id"])) if status_map else None) or "new"
        order_status = FbsOrderStatus.CONFIRM.value if raw_status == "confirm" else FbsOrderStatus.NEW.value

        created_at = self._parse_created_at(task.get("createdAt"))
        order = FbsOrder(
            order_uid=str(task.get("orderUid")),
            status=order_status,
            created_at=created_at,
            sla_deadline=created_at + timedelta(hours=120),
            warehouse_id=wh_id,
            warehouse_name=wh_name,
            cargo_type=task.get("cargoType", 1),
            is_pvz_allowed=task.get("isPickupPointShipmentAllowed", True),
            is_b2b=bool((task.get("options") or {}).get("isB2B", False))
        )
        self.db.add(order)
        self.db.flush()
        return order

    def _create_order_item(self, task: dict[str, Any], order_id: int, products_map: dict[str, Product]) -> None:
        skus = task.get("skus", [])
        barcode = str(skus[0]).strip() if skus else ""
        product = products_map.get(barcode)
        price = float(task.get("convertedPrice", task.get("price", 0))) / 100.0

        item = FbsOrderItem(
            task_id=str(task.get("id")),
            rid=task.get("rid"),
            order_id=order_id,
            product_id=product.id if product else None,
            barcode=barcode or (product.barcode if product else "—"),
            article=product.article if product else task.get("article", "—"),
            group_name=product.group_name if product else "Общее",
            price=price,
            stock_written_off=False
        )
        self.db.add(item)
        if product:
            InventoryEngine.reserve(self.db, product.id, quantity=1, task_id=str(task.get("id")))

    @staticmethod
    def _parse_created_at(created_at_str: str | None) -> datetime:
        if not created_at_str:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return datetime.utcnow()