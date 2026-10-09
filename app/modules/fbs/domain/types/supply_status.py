# app/modules/fbs/domain/types/supply_status.py

from enum import Enum


class FbsSupplyStatus(str, Enum):
    """Внутренние системные статусы поставки/коробки."""
    IN_ASSEMBLY = "in_assembly"      # Открыта, формируется на складе
    PROCESSING = "processing"        # Передана в доставку (едет на СЦ WB)
    DELIVERED = "delivered"          # Принята на складе WB
    MISSING_ON_WB = "missing_on_wb"  # Не найдена в личном кабинете WB