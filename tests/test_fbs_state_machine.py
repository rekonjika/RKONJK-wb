# tests/test_fbs_state_machine.py

from app.modules.fbs.domain.types.wb_status import WbStatusResolver


def test_wb_status_resolver_cancels_declined_by_client() -> None:
    """Проверка критического бага WB: declined_by_client обязан отменять заказ даже при supplierStatus: 'new'."""
    assert WbStatusResolver.is_cancelled(supplier_status="new", wb_status="declined_by_client") is True
    assert WbStatusResolver.is_cancelled(supplier_status="confirm", wb_status="canceled_by_client") is True
    assert WbStatusResolver.is_cancelled(supplier_status="cancel", wb_status="waiting") is True


def test_wb_status_resolver_active_orders() -> None:
    """Активный заказ не должен считаться отмененным."""
    assert WbStatusResolver.is_cancelled(supplier_status="new", wb_status="waiting") is False
    assert WbStatusResolver.is_cancelled(supplier_status="confirm", wb_status="sorted") is False


def test_wb_status_resolver_completed_orders() -> None:
    """Проверка определения успешного вручения заказа."""
    assert WbStatusResolver.is_completed(supplier_status="complete", wb_status="waiting") is True
    assert WbStatusResolver.is_completed(supplier_status="new", wb_status="sold") is True