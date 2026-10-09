# app/modules/fbs/use_cases/order/cancel/handler.py

import logging
from sqlalchemy.orm import Session
from app.modules.fbs.domain.models.order_item import FbsOrderItem
from app.modules.fbs.domain.types.order_status import FbsOrderStatus
from app.modules.inventory.domain.services.inventory_engine import InventoryEngine
from app.modules.fbs.use_cases.order.cancel.dto import CancelOrderDTO

logger = logging.getLogger("cancel_order_handler")


class CancelOrderHandler:
    def __init__(self, db: Session) -> None:
        self.db = db

    def handle(self, dto: CancelOrderDTO) -> bool:
        item = self.db.query(FbsOrderItem).filter(FbsOrderItem.task_id == dto.task_id).first()
        if not item or not item.order:
            logger.warning(f"[Cancel] Задание {dto.task_id} не найдено в БД.")
            return False

        if item.order.status == FbsOrderStatus.CANCELLED.value:
            return True

        if item.product_id:
            InventoryEngine.release(self.db, item.product_id, quantity=1, task_id=item.task_id)

        item.order.status = FbsOrderStatus.CANCELLED.value
        if item.supply and item.supply.status == "in_assembly":
            item.supply_id = None

        self.db.commit()
        logger.info(f"[Cancel Success] Заказ {dto.task_id} отменен. Причина: {dto.reason}")
        return True