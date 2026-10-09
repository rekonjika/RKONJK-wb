# app/modules/inventory/domain/models/stock.py

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.catalog.domain.models.product import Product


class WarehouseStock(Base):
    """Физическое наличие товара на складе и сумма активной брони."""
    __tablename__ = "warehouse_stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )

    physical_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    product: Mapped["Product"] = relationship("Product", back_populates="stock")

    @property
    def available_quantity(self) -> int:
        """Доступно для продажи на витринах маркетплейсов."""
        return max(0, self.physical_quantity - self.reserved_quantity)

    def __repr__(self) -> str:
        return f"<WarehouseStock product_id={self.product_id} phys={self.physical_quantity} res={self.reserved_quantity}>"