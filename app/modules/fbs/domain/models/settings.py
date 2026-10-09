# app/modules/fbs/domain/models/settings.py

from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.catalog.domain.models.product import Product


class FbsWarehouseProductSetting(Base):
    """Настройки выгрузки и связки chrt_id карточки с конкретным складом WB."""
    __tablename__ = "fbs_warehouse_product_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    barcode: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    product_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), index=True, nullable=True)
    wb_warehouse_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)

    chrt_id: Mapped[int | None] = mapped_column(BigInteger, index=True, nullable=True)
    nm_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_stock: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_threshold: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    wb_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    product: Mapped["Product | None"] = relationship("Product", back_populates="wb_settings")

    __table_args__ = (
        UniqueConstraint("barcode", "wb_warehouse_id", name="uq_barcode_wh"),
    )