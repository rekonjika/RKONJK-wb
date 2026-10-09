# app/modules/fbo/domain/models/fbo.py

from sqlalchemy import BigInteger, Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class WarehouseTier(Base):
    """Приоритеты складов WB для поставок FBO."""
    __tablename__ = "warehouse_tiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    warehouse_name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    tier: Mapped[int] = mapped_column(Integer, default=1)
    priority: Mapped[int] = mapped_column(Integer, default=1)
    coefficient: Mapped[float] = mapped_column(Float, default=1.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class WbStock(Base):
    """Аналитические остатки на складах WB для FBO."""
    __tablename__ = "wb_stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    barcode: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    nm_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    article: Mapped[str | None] = mapped_column(String(255), nullable=True)
    subject_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    warehouse_name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    reserved: Mapped[int] = mapped_column(Integer, default=0)


class Supply(Base):
    """Поставки FBO."""
    __tablename__ = "supplies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_number: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    wb_order_id: Mapped[str | None] = mapped_column(String(100), index=True, nullable=True)
    barcode: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    target_warehouse: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="0")