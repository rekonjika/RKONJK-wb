# app/modules/fbs/use_cases/supply/sync/handler.py

import logging
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.wb_client import WildberriesClient
from app.modules.fbs.domain.models.order_item import FbsOrderItem
from app.modules.fbs.domain.models.supply import FbsSupply
from app.modules.fbs.domain.types.supply_status import FbsSupplyStatus
from app.modules.inventory.domain.services.inventory_engine import InventoryEngine

logger = logging.getLogger("sync_supplies_handler")


class SyncSuppliesHandler:
    def __init__(self, db: Session, client: WildberriesClient) -> None:
        self.db = db
        self.client = client

    def handle(self) -> int:
        wb_supplies_list = self._fetch_all_supplies()
        if not wb_supplies_list:
            return 0

        wb_existing_ids = {s["id"] for s in wb_supplies_list if s.get("id")}
        self._cleanup_dead_supplies(wb_existing_ids)

        wh_map = {int(w["id"]): w.get("name") for w in self.client.get_warehouses()}

        for sup in wb_supplies_list:
            wb_sup_id = sup.get("id")
            if not wb_sup_id:
                continue

            db_sup = self._upsert_supply(sup, wb_sup_id, wh_map)
            if not sup.get("done", False):
                self._bind_supply_orders(wb_sup_id, db_sup.id)

        self.db.commit()
        return len(wb_existing_ids)

    def _fetch_all_supplies(self) -> list[dict[str, Any]]:
        wb_supplies: list[dict[str, Any]] = []
        next_cursor = 0
        while True:
            data = self.client.get_supplies(next_cursor=next_cursor, limit=1000)
            page = data.get("supplies", [])
            wb_supplies.extend(page)
            next_val = data.get("next", 0)
            if not next_val or len(page) < 1000:
                break
            next_cursor = next_val
        return wb_supplies

    def _cleanup_dead_supplies(self, existing_ids: set[str]) -> None:
        dead = self.db.query(FbsSupply).filter(
            FbsSupply.wb_supply_id.isnot(None),
            FbsSupply.wb_supply_id.notin_(list(existing_ids))
        ).all()
        for s in dead:
            self.db.query(FbsOrderItem).filter(FbsOrderItem.supply_id == s.id).update(
                {"supply_id": None}, synchronize_session=False
            )
            self.db.delete(s)

    def _upsert_supply(self, sup: dict[str, Any], wb_sup_id: str, wh_map: dict[int, str | None]) -> FbsSupply:
        is_done = sup.get("done", False)
        target_st = FbsSupplyStatus.PROCESSING.value if is_done else FbsSupplyStatus.IN_ASSEMBLY.value
        wh_id = int(sup["warehouseId"]) if sup.get("warehouseId") else None
        wh_name = wh_map.get(wh_id) if wh_id else (sup.get("warehouseName") or "—")

        db_sup = self.db.query(FbsSupply).filter(FbsSupply.wb_supply_id == wb_sup_id).first()
        if db_sup:
            if is_done and db_sup.status == FbsSupplyStatus.IN_ASSEMBLY.value:
                self._write_off_supply_items(db_sup.id)
            db_sup.status = target_st
        else:
            db_sup = FbsSupply(
                wb_supply_id=wb_sup_id,
                shipment_name=sup.get("name") or f"Поставка {wb_sup_id}",
                qr_code=f"WB-GI-{wb_sup_id.replace('WB-GI-', '')}",
                status=target_st,
                warehouse_name=wh_name,
                warehouse_id=wh_id,
                is_mgt=True
            )
            self.db.add(db_sup)
            self.db.flush()
        return db_sup

    def _write_off_supply_items(self, supply_id: int) -> None:
        items = self.db.query(FbsOrderItem).filter(FbsOrderItem.supply_id == supply_id).all()
        for it in items:
            if it.product_id and not it.stock_written_off:
                InventoryEngine.write_off(self.db, it.product_id, quantity=1, task_id=it.task_id)
                it.stock_written_off = True

    def _bind_supply_orders(self, wb_sup_id: str, local_supply_id: int) -> None:
        order_ids = self.client.get_supply_order_ids(wb_sup_id)
        if not order_ids:
            return
        t_ids = [str(tid) for tid in order_ids]

        self.db.query(FbsOrderItem).filter(
            FbsOrderItem.supply_id == local_supply_id,
            FbsOrderItem.task_id.notin_(t_ids)
        ).update({"supply_id": None}, synchronize_session=False)

        self.db.query(FbsOrderItem).filter(
            FbsOrderItem.task_id.in_(t_ids)
        ).update({"supply_id": local_supply_id}, synchronize_session=False)

        self.db.execute(
            text("""
                UPDATE fbs_orders
                SET status = 'confirm'
                WHERE id IN (
                    SELECT DISTINCT order_id FROM fbs_order_items WHERE supply_id = :sup_id
                ) AND status = 'new'
            """),
            {"sup_id": local_supply_id}
        )