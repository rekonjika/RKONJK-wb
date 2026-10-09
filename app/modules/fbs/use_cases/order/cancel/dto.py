# app/modules/fbs/use_cases/order/cancel/dto.py

from pydantic import BaseModel


class CancelOrderDTO(BaseModel):
    task_id: str
    reason: str = "Client or system cancellation"