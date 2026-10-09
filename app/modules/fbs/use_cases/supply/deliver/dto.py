# app/modules/fbs/use_cases/supply/deliver/dto.py

from pydantic import BaseModel


class DeliverSupplyDTO(BaseModel):
    supply_id: int