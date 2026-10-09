# app/modules/fbs/use_cases/supply/create/dto.py

from pydantic import BaseModel, Field


class CreateSupplyDTO(BaseModel):
    shipment_name: str = Field(..., description="Название коробки/поставки")
    warehouse_id: int = Field(..., description="ID склада WB")
    order_uids: list[str] = Field(..., min_length=1)