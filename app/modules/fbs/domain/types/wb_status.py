# app/modules/fbs/domain/types/wb_status.py

class WbStatusResolver:

    CANCEL_WB_STATUSES: set[str] = {
        "canceled",
        "canceled_by_client",
        "declined_by_client",
        "defect",
        "canceled_by_carrier"
    }

    CANCEL_SUPPLIER_STATUSES: set[str] = {
        "cancel",
        "cancel_carrier"
    }

    COMPLETED_WB_STATUSES: set[str] = {
        "sold",
        "ready_for_pickup"
    }

    @classmethod
    def is_cancelled(cls, supplier_status: str | None, wb_status: str | None) -> bool:
        """Отмена WB всегда перебивает supplierStatus == 'new'."""
        if wb_status and wb_status.lower() in cls.CANCEL_WB_STATUSES:
            return True
        if supplier_status and supplier_status.lower() in cls.CANCEL_SUPPLIER_STATUSES:
            return True
        return False

    @classmethod
    def is_completed(cls, supplier_status: str | None, wb_status: str | None) -> bool:
        """Заказ успешно вручен или готов к выдаче."""
        if supplier_status == "complete":
            return True
        if wb_status and wb_status.lower() in cls.COMPLETED_WB_STATUSES:
            return True
        return False