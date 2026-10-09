# app/modules/fbs/domain/models/sticker.py

from datetime import datetime
from typing import TYPE_CHECKING
from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.modules.fbs.domain.models.order_item import FbsOrderItem


class FbsOrderSticker(Base):
    """Изолированная таблица для хранения тяжелых Base64-стикеров 58x40."""
    __tablename__ = "fbs_order_stickers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_item_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("fbs_order_items.id", ondelete="CASCADE"), unique=True, index=True, nullable=False
    )
    task_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    sticker_type: Mapped[str] = mapped_column(String(20), default="png")
    file_base64: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    item: Mapped["FbsOrderItem"] = relationship("FbsOrderItem", back_populates="sticker")