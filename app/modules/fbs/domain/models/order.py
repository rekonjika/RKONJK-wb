# app/modules/fbs/domain/models/order.py

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import BigInteger, Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.fbs.domain.models.order_item import FbsOrderItem


class FbsOrder(Base):
    """Шапка заказа FBS маркетплейса."""
    __tablename__ = "fbs_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_uid: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="new", index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    sla_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)

    warehouse_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    warehouse_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(255), nullable=True)

    cargo_type: Mapped[int] = mapped_column(Integer, default=1)
    is_pvz_allowed: Mapped[bool] = mapped_column(Boolean, default=True)
    is_b2b: Mapped[bool] = mapped_column(Boolean, default=False)

    items: Mapped[list["FbsOrderItem"]] = relationship(
        "FbsOrderItem", back_populates="order", cascade="all, delete-orphan"
    )