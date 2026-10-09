# app/modules/fbs/use_cases/order/sticker/dto.py

from typing import Any
from pydantic import BaseModel


class FetchStickersDTO(BaseModel):
    orders: list[Any]
    type: str = "png"
    width: int = 58
    height: int = 40