# app/modules/fbs/use_cases/stock/zero_stock/dto.py

from pydantic import BaseModel, Field


class ZeroStockDTO(BaseModel):
    warehouse_id: int = Field(..., description="ID склада WB")
    barcodes: list[str] | None = None