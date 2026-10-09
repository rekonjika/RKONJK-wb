# app/modules/fbs/domain/models/order_item.py

from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.catalog.domain.models.product import Product
    from app.modules.fbs.domain.models.order import FbsOrder
    from app.modules.fbs.domain.models.supply import FbsSupply
    from app.modules.fbs.domain.models.sticker import FbsOrderSticker


class FbsOrderItem(Base):
    """Позиция (сборочное задание) в заказе."""
    __tablename__ = "fbs_order_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    rid: Mapped[str | None] = mapped_column(String(100), nullable=True)

    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("fbs_orders.id", ondelete="CASCADE"), index=True, nullable=False)
    supply_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("fbs_supplies.id", ondelete="SET NULL"), index=True, nullable=True)
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("products.id", ondelete="SET NULL"), index=True, nullable=True)

    barcode: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    article: Mapped[str | None] = mapped_column(String(255), nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    price: Mapped[float] = mapped_column(Float, default=0.0)

    part_a: Mapped[str | None] = mapped_column(String(50), nullable=True)
    part_b: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sticker_base64: Mapped[str | None] = mapped_column(Text, nullable=True)
    stock_written_off: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    order: Mapped["FbsOrder"] = relationship("FbsOrder", back_populates="items")
    supply: Mapped["FbsSupply | None"] = relationship("FbsSupply", back_populates="items")
    product: Mapped["Product | None"] = relationship("Product", back_populates="order_items")
    sticker: Mapped["FbsOrderSticker | None"] = relationship("FbsOrderSticker", back_populates="item", uselist=False, cascade="all, delete-orphan")