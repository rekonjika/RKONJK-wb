# tests/test_stock_calculations.py

from app.modules.fbs.use_cases.stock.push_delta.handler import PushDeltaStocksHandler


def test_buffer_calculation_threshold_two_or_less() -> None:
    """При остатке <= 2 штук витрина WB должна обнуляться для защиты от оверсейла."""
    assert PushDeltaStocksHandler._calculate_target_stock(real_available=2, safety_stock=0, max_stock=None) == 0
    assert PushDeltaStocksHandler._calculate_target_stock(real_available=1, safety_stock=0, max_stock=None) == 0


def test_buffer_calculation_medium_stock() -> None:
    """Для остатка от 16 до 100 выставляется 80% за вычетом 10% буфера."""
    # 50 - ceil(5) = 45 -> floor(45 * 0.8) = 36
    target = PushDeltaStocksHandler._calculate_target_stock(real_available=50, safety_stock=0, max_stock=None)
    assert target == 36


def test_buffer_calculation_max_stock_limit() -> None:
    """Лимит max_stock обязан ограничивать выставление на витрину."""
    target = PushDeltaStocksHandler._calculate_target_stock(real_available=200, safety_stock=0, max_stock=10)
    assert target == 10