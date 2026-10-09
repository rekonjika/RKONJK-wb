# app/modules/fbs/use_cases/supply/deliver/handler.py

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.core.wb_client import WildberriesClient
from app.modules.fbs.domain.models.order_item import FbsOrderItem
from app.modules.fbs.domain.models.supply import FbsSupply
from app.modules.fbs.domain.types.order_status import FbsOrderStatus
from app.modules.fbs.domain.types.supply_status import FbsSupplyStatus
from app.modules.inventory.domain.services.inventory_engine import InventoryEngine
from app.modules.fbs.use_cases.supply.deliver.dto import DeliverSupplyDTO

logger = logging.getLogger("deliver_supply_handler")


class DeliverSupplyHandler:
    def __init__(self, db: Session, client: WildberriesClient) -> None:
        self.db = db
        self.client = client

    def handle(self, dto: DeliverSupplyDTO) -> bool:
        supply = self.db.query(FbsSupply).filter(FbsSupply.id == dto.supply_id).with_for_update().first()
        if not supply or not supply.wb_supply_id:
            return False

        if supply.status != FbsSupplyStatus.IN_ASSEMBLY.value:
            return supply.status == FbsSupplyStatus.PROCESSING.value

        if not self.client.deliver_supply(supply.wb_supply_id):
            return False

        supply.status = FbsSupplyStatus.PROCESSING.value
        supply.scan_date = datetime.utcnow()

        # Физическое списание остатка через InventoryEngine
        items = self.db.query(FbsOrderItem).filter(FbsOrderItem.supply_id == supply.id).all()
        for it in items:
            if it.product_id and it.order and it.order.status != FbsOrderStatus.CANCELLED.value:
                if not it.stock_written_off:
                    InventoryEngine.write_off(self.db, it.product_id, quantity=1, task_id=it.task_id)
                    it.stock_written_off = True

        self.db.commit()
        return True