# app/modules/fbs/domain/types/order_status.py

from enum import Enum


class FbsOrderStatus(str, Enum):
    """Внутренние системные статусы заказа в WMS."""
    NEW = "new"                  # Новый, поступил в обработку
    CONFIRM = "confirm"          # Подтвержден / упакован в поставку
    IN_ASSEMBLY = "in_assembly"  # На комплектации сборщиком
    COMPLETED = "completed"      # Доставлен покупателю
    CANCELLED = "cancelled"      # Отменен покупателем или складом

    @classmethod
    def active_statuses(cls) -> list[str]:
        return [cls.NEW.value, cls.CONFIRM.value, cls.IN_ASSEMBLY.value]