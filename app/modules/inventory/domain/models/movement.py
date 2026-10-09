# app/modules/inventory/domain/models/movement.py

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING
from sqlalchemy import Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.catalog.domain.models.product import Product


class StockMovementType(str, Enum):
    IMPORT = "IMPORT"                # Приход / Инвентаризация через Excel
    RESERVE = "RESERVE"              # Бронь под новый заказ FBS
    RELEASE = "RELEASE"              # Снятие брони при отмене заказа
    WRITE_OFF = "WRITE_OFF"          # Физическое списание при отгрузке поставки
    MANUAL_ADJUST = "MANUAL_ADJUST"  # Ручная корректировка кладовщиком


class StockMovement(Base):
    """Неизменяемый журнал движений (Ledger / Audit Log)."""
    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=False
    )
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    order_task_id: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    comment: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    product: Mapped["Product"] = relationship("Product", back_populates="movements")