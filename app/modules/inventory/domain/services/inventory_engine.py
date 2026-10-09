# app/modules/inventory/domain/services/inventory_engine.py

import logging
from sqlalchemy.orm import Session
from app.modules.inventory.domain.models.stock import WarehouseStock
from app.modules.inventory.domain.models.movement import StockMovement, StockMovementType

logger = logging.getLogger("inventory_engine")


class InventoryEngine:
    """
    Транзакционный движок управления остатками склада.
    Гарантирует блокировку строк (SELECT FOR UPDATE) и запись в журнал аудита.
    """

    @classmethod
    def reserve(cls, db: Session, product_id: int, quantity: int = 1, task_id: str | None = None) -> bool:
        """Бронирует товар под сборочное задание FBS."""
        stock = db.query(WarehouseStock).filter(WarehouseStock.product_id == product_id).with_for_update().first()
        if not stock:
            return False

        stock.reserved_quantity += quantity
        db.add(StockMovement(
            product_id=product_id,
            delta=quantity,
            movement_type=StockMovementType.RESERVE.value,
            order_task_id=task_id,
            comment=f"Бронь под сборочное задание #{task_id or '—'}"
        ))
        db.flush()  # Фиксируем изменения в текущей транзакции
        return True

    @classmethod
    def release(cls, db: Session, product_id: int, quantity: int = 1, task_id: str | None = None) -> bool:
        """Снимает бронь при отмене заказа покупателем."""
        stock = db.query(WarehouseStock).filter(WarehouseStock.product_id == product_id).with_for_update().first()
        if not stock:
            return False

        stock.reserved_quantity = max(0, stock.reserved_quantity - quantity)
        db.add(StockMovement(
            product_id=product_id,
            delta=-quantity,
            movement_type=StockMovementType.RELEASE.value,
            order_task_id=task_id,
            comment=f"Снятие брони при отмене #{task_id or '—'}"
        ))
        db.flush()
        return True

    @classmethod
    def write_off(cls, db: Session, product_id: int, quantity: int = 1, task_id: str | None = None) -> bool:
        """Физически списывает остаток со склада при передаче поставки в доставку."""
        stock = db.query(WarehouseStock).filter(WarehouseStock.product_id == product_id).with_for_update().first()
        if not stock:
            return False

        stock.physical_quantity = max(0, stock.physical_quantity - quantity)
        stock.reserved_quantity = max(0, stock.reserved_quantity - quantity)

        db.add(StockMovement(
            product_id=product_id,
            delta=-quantity,
            movement_type=StockMovementType.WRITE_OFF.value,
            order_task_id=task_id,
            comment=f"Списание при отгрузке поставки #{task_id or '—'}"
        ))
        db.flush()
        return True