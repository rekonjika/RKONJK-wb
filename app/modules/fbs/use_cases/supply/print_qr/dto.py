# app/modules/fbs/use_cases/supply/print_qr/dto.py

from typing import Literal
from pydantic import BaseModel, Field


class SupplyBarcodeDTO(BaseModel):
    supply_id: int = Field(..., description="ID поставки в локальной БД")
    type: Literal["svg", "zplv", "zplh", "png"] = Field("png")