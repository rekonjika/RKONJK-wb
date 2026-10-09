# app/core/wb_client/__init__.py

from typing import Any
from app.core.wb_client.content_api import ContentApi
from app.core.wb_client.marketplace_api import MarketplaceApi


class WildberriesClient:
    """
    Фасадный SDK-клиент Wildberries API по стандартам baks-dev.
    Объединяет Marketplace и Content API в единую удобную точку входа.
    """

    def __init__(self, token: str) -> None:
        clean_token = token.strip()
        self.marketplace = MarketplaceApi(clean_token)
        self.content = ContentApi(clean_token)

    # Делегирование методов складов
    def get_warehouses(self) -> list[dict[str, Any]]:
        return self.marketplace.get_warehouses()

    # Делегирование методов остатков
    def update_stocks(self, warehouse_id: int, stocks: list[dict[str, Any]]) -> bool:
        return self.marketplace.update_stocks(warehouse_id, stocks)

    def get_live_stocks(self, warehouse_id: int, chrt_ids: list[int]) -> list[dict[str, Any]]:
        return self.marketplace.get_live_stocks(warehouse_id, chrt_ids)

    # Делегирование методов заказов
    def get_new_orders(self) -> list[dict[str, Any]]:
        return self.marketplace.get_new_orders()

    def get_orders_cursor(self, date_from_ts: int, next_cursor: int = 0, limit: int = 1000) -> dict[str, Any]:
        return self.marketplace.get_orders_cursor(date_from_ts, next_cursor, limit)

    def get_orders_statuses(self, order_ids: list[int]) -> list[dict[str, Any]]:
        return self.marketplace.get_orders_statuses(order_ids)

    def get_stickers(
        self,
        order_ids: list[int],
        sticker_type: str = "png",
        width: int = 58,
        height: int = 40
    ) -> list[dict[str, Any]]:
        return self.marketplace.get_stickers(order_ids, sticker_type, width, height)

    # Делегирование методов поставок
    def get_supplies(self, next_cursor: int = 0, limit: int = 1000) -> dict[str, Any]:
        return self.marketplace.get_supplies(next_cursor, limit)

    def create_supply(self, name: str) -> str | None:
        return self.marketplace.create_supply(name)

    def add_orders_to_supply(self, wb_supply_id: str, task_ids: list[int]) -> bool:
        return self.marketplace.add_orders_to_supply(wb_supply_id, task_ids)

    def get_supply_order_ids(self, wb_supply_id: str) -> list[int]:
        return self.marketplace.get_supply_order_ids(wb_supply_id)

    def get_supply_orders(self, wb_supply_id: str) -> list[dict[str, Any]]:
        return self.marketplace.get_supply_orders(wb_supply_id)

    def deliver_supply(self, wb_supply_id: str) -> bool:
        return self.marketplace.deliver_supply(wb_supply_id)

    def get_supply_barcode(self, wb_supply_id: str, barcode_type: str = "png") -> dict[str, Any] | None:
        return self.marketplace.get_supply_barcode(wb_supply_id, barcode_type)

    # Делегирование методов контента
    def get_cards_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self.content.get_cards_list(payload)


__all__ = ["WildberriesClient", "MarketplaceApi", "ContentApi"]