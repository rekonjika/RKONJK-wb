# app/modules/fbs/use_cases/supply/create/handler.py

import logging
from sqlalchemy.orm import Session
from app.core.wb_client import WildberriesClient
from app.modules.fbs.domain.models.order import FbsOrder
from app.modules.fbs.domain.models.order_item import FbsOrderItem
from app.modules.fbs.domain.models.supply import FbsSupply
from app.modules.fbs.domain.types.order_status import FbsOrderStatus
from app.modules.fbs.domain.types.supply_status import FbsSupplyStatus
from app.modules.fbs.use_cases.supply.create.dto import CreateSupplyDTO

logger = logging.getLogger("create_supply_handler")


class CreateSupplyHandler:
    def __init__(self, db: Session, client: WildberriesClient) -> None:
        self.db = db
        self.client = client

    def handle(self, dto: CreateSupplyDTO) -> FbsSupply | None:
        clean_uids = list(dict.fromkeys([str(u).strip() for u in dto.order_uids if str(u).strip()]))
        items = (
            self.db.query(FbsOrderItem)
            .join(FbsOrder, FbsOrderItem.order_id == FbsOrder.id)
            .filter(FbsOrder.order_uid.in_(clean_uids))
            .all()
        )
        task_ids = [int(i.task_id) for i in items if i.task_id and str(i.task_id).strip().isdigit()]
        if not task_ids:
            return None

        wb_supply_id = self.client.create_supply(dto.shipment_name)
        if not wb_supply_id:
            return None

        for i in range(0, len(task_ids), 100):
            if not self.client.add_orders_to_supply(wb_supply_id, task_ids[i:i + 100]):
                return None

        warehouses = self.client.get_warehouses()
        wh_name = next((w.get("name") for w in warehouses if int(w["id"]) == dto.warehouse_id), "Склад FBS")

        supply = FbsSupply(
            wb_supply_id=wb_supply_id,
            shipment_name=dto.shipment_name,
            qr_code=f"WB-GI-{wb_supply_id.replace('WB-GI-', '')}",
            status=FbsSupplyStatus.IN_ASSEMBLY.value,
            warehouse_name=wh_name,
            warehouse_id=dto.warehouse_id,
            is_mgt=True
        )
        self.db.add(supply)
        self.db.flush()

        for it in items:
            it.supply_id = supply.id
            if it.order and it.order.status == FbsOrderStatus.NEW.value:
                it.order.status = FbsOrderStatus.CONFIRM.value

        self.db.commit()
        self.db.refresh(supply)
        return supply