# app/modules/fbs/use_cases/stock/push_delta/dto.py

from pydantic import BaseModel


class PushStocksDTO(BaseModel):
    warehouse_id: int | None = None