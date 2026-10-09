# app/modules/inventory/domain/models/import_log.py

from datetime import datetime
from typing import Any
from sqlalchemy import Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class WarehouseImportLog(Base):
    """Логирование загрузок файлов остатков."""
    __tablename__ = "warehouse_import_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    items_count: Mapped[int] = mapped_column(Integer, default=0)
    box: Mapped[int] = mapped_column(Integer, default=0)
    pallet: Mapped[int] = mapped_column(Integer, default=0)
    file_data: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON, nullable=True)