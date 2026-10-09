# tests/test_inventory_engine.py

from sqlalchemy.orm import Session

from app.modules.catalog.domain.models.product import Product
from app.modules.inventory.domain.models.movement import StockMovement, StockMovementType
from app.modules.inventory.domain.models.stock import WarehouseStock
from app.modules.inventory.domain.services.inventory_engine import InventoryEngine


def test_inventory_reserve_and_release(db_session: Session) -> None:
    """Проверка бронирования, снятия брони и формирования записей в Ledger."""
    prod = Product(barcode="200000000001", article="ART-1")
    db_session.add(prod)
    db_session.flush()

    stock = WarehouseStock(product_id=prod.id, physical_quantity=10, reserved_quantity=0)
    db_session.add(stock)
    db_session.flush()

    # 1. Бронь
    assert InventoryEngine.reserve(db_session, product_id=prod.id, quantity=2, task_id="TASK-1") is True
    assert stock.reserved_quantity == 2
    assert stock.available_quantity == 8

    # 2. Снятие брони
    assert InventoryEngine.release(db_session, product_id=prod.id, quantity=1, task_id="TASK-1") is True
    assert stock.reserved_quantity == 1
    assert stock.available_quantity == 9

    # 3. Проверка записей в журнале движений (Ledger)
    movements = (
        db_session.query(StockMovement)
        .filter(StockMovement.product_id == prod.id)
        .order_by(StockMovement.id.asc())
        .all()
    )
    assert len(movements) == 2
    assert movements[0].movement_type == StockMovementType.RESERVE.value
    assert movements[0].delta == 2
    assert movements[1].movement_type == StockMovementType.RELEASE.value
    assert movements[1].delta == -1