# app/modules/catalog/domain/models/product.py

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import String, Float, Integer, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.inventory.domain.models.stock import WarehouseStock
    from app.modules.inventory.domain.models.movement import StockMovement
    from app.modules.fbs.domain.models.settings import FbsWarehouseProductSetting
    from app.modules.fbs.domain.models.order_item import FbsOrderItem


class Product(Base):
    """Справочник товаров (номенклатура). Только паспортные данные карточки."""
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    barcode: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    article: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    brand: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    group_name: Mapped[str | None] = mapped_column(String(255), nullable=True, default="—")
    photo_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    multiplicity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    speed: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Связи с другими доменами
    stock: Mapped["WarehouseStock | None"] = relationship(
        "WarehouseStock", back_populates="product", uselist=False, cascade="all, delete-orphan"
    )
    movements: Mapped[list["StockMovement"]] = relationship(
        "StockMovement", back_populates="product", cascade="all, delete-orphan"
    )
    wb_settings: Mapped[list["FbsWarehouseProductSetting"]] = relationship(
        "FbsWarehouseProductSetting", back_populates="product", cascade="all, delete-orphan"
    )
    order_items: Mapped[list["FbsOrderItem"]] = relationship(
        "FbsOrderItem", back_populates="product"
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} barcode={self.barcode} article={self.article}>"