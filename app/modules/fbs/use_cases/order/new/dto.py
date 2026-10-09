# app/modules/fbs/use_cases/order/new/dto.py

from typing import Any
from pydantic import BaseModel


class RawWbOrderDTO(BaseModel):
    id: int
    orderUid: str
    createdAt: str
    warehouseId: int | None = None
    rid: str | None = None
    cargoType: int = 1
    isPickupPointShipmentAllowed: bool = True
    price: float = 0.0
    convertedPrice: float = 0.0
    skus: list[str] = []
    article: str | None = None
    options: dict[str, Any] | None = None