# app/modules/fbs/domain/models/supply.py

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.fbs.domain.models.order_item import FbsOrderItem


class FbsSupply(Base):
    """Поставка / Коробка сборочных заданий FBS."""
    __tablename__ = "fbs_supplies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wb_supply_id: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    shipment_name: Mapped[str] = mapped_column(String(255), nullable=False)
    qr_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="in_assembly", index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    scan_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    warehouse_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    warehouse_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_mgt: Mapped[bool] = mapped_column(Boolean, default=True)

    items: Mapped[list["FbsOrderItem"]] = relationship("FbsOrderItem", back_populates="supply")