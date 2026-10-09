# app/core/wb_client/marketplace_api.py

from typing import Any
from app.core.wb_client.base import BaseWbClient


class MarketplaceApi(BaseWbClient):
    """Методы Wildberries Marketplace API v3 (Склады, Остатки, Заказы, Поставки)."""

    BASE_URL = "https://marketplace-api.wildberries.ru"

    # --- СКЛАДЫ ---
    def get_warehouses(self) -> list[dict[str, Any]]:
        """GET /api/v3/warehouses — Список FBS-складов продавца."""
        url = f"{self.BASE_URL}/api/v3/warehouses"
        res = self.request("GET", url, timeout=(5, 10))
        return res.json() if res.status_code == 200 else []

    # --- ОСТАТКИ ---
    def update_stocks(self, warehouse_id: int, stocks: list[dict[str, Any]]) -> bool:
        """PUT /api/v3/stocks/{warehouseId} — Дельта-выгрузка остатков."""
        url = f"{self.BASE_URL}/api/v3/stocks/{warehouse_id}"
        res = self.request("PUT", url, json={"stocks": stocks})
        return res.status_code in (200, 204)

    def get_live_stocks(self, warehouse_id: int, chrt_ids: list[int]) -> list[dict[str, Any]]:
        """POST /api/v3/stocks/{warehouseId} — Живая сверка факта витрины."""
        url = f"{self.BASE_URL}/api/v3/stocks/{warehouse_id}"
        res = self.request("POST", url, json={"chrtIds": chrt_ids})
        return res.json().get("stocks", []) if res.status_code == 200 else []

    # --- СБОРОЧНЫЕ ЗАДАНИЯ (ЗАКАЗЫ) ---
    def get_new_orders(self) -> list[dict[str, Any]]:
        """GET /api/v3/orders/new — Быстрый забор свежих сборочных заданий."""
        url = f"{self.BASE_URL}/api/v3/orders/new"
        res = self.request("GET", url, timeout=(5, 25))
        return res.json().get("orders", []) if res.status_code == 200 else []

    def get_orders_cursor(self, date_from_ts: int, next_cursor: int = 0, limit: int = 1000) -> dict[str, Any]:
        """GET /api/v3/orders — Курсорная пагинация по архиву заказов (Карусель)."""
        url = f"{self.BASE_URL}/api/v3/orders"
        params = {"limit": limit, "next": next_cursor, "dateFrom": date_from_ts}
        res = self.request("GET", url, params=params, timeout=(5, 25))
        return res.json() if res.status_code == 200 else {"orders": [], "next": 0}

    def get_orders_statuses(self, order_ids: list[int]) -> list[dict[str, Any]]:
        """POST /api/v3/orders/status — Сверка статусов и отмен (до 200 ID за раз)."""
        url = f"{self.BASE_URL}/api/v3/orders/status"
        res = self.request("POST", url, json={"orders": order_ids}, timeout=(5, 15))
        return res.json().get("orders", []) if res.status_code == 200 else []

    def get_stickers(
        self,
        order_ids: list[int],
        sticker_type: str = "png",
        width: int = 58,
        height: int = 40
    ) -> list[dict[str, Any]]:
        """POST /api/v3/orders/stickers — Получение стикеров сборочных заданий (до 100 ID)."""
        url = f"{self.BASE_URL}/api/v3/orders/stickers"
        params = {"type": sticker_type, "width": width, "height": height}
        res = self.request("POST", url, params=params, json={"orders": order_ids}, timeout=(5, 15))
        return res.json().get("stickers", []) if res.status_code == 200 else []

    # --- ПОСТАВКИ (КОРОБКИ) ---
    def get_supplies(self, next_cursor: int = 0, limit: int = 1000) -> dict[str, Any]:
        """GET /api/v3/supplies — Список поставок продавца."""
        url = f"{self.BASE_URL}/api/v3/supplies"
        res = self.request("GET", url, params={"limit": limit, "next": next_cursor}, timeout=(5, 15))
        return res.json() if res.status_code == 200 else {"supplies": [], "next": 0}

    def create_supply(self, name: str) -> str | None:
        """POST /api/v3/supplies — Создание новой открытой поставки."""
        url = f"{self.BASE_URL}/api/v3/supplies"
        res = self.request("POST", url, json={"name": name}, timeout=(5, 10))
        return res.json().get("id") if res.status_code in (200, 201) else None

    def add_orders_to_supply(self, wb_supply_id: str, task_ids: list[int]) -> bool:
        """PATCH /api/marketplace/v3/supplies/{supplyId}/orders — Привязка заданий к поставке."""
        url = f"{self.BASE_URL}/api/marketplace/v3/supplies/{wb_supply_id}/orders"
        res = self.request("PATCH", url, json={"orders": task_ids}, timeout=(5, 15))
        return res.status_code in (200, 204)

    def get_supply_order_ids(self, wb_supply_id: str) -> list[int]:
        """GET /api/marketplace/v3/supplies/{supplyId}/order-ids — Быстрое получение массива ID заданий."""
        url = f"{self.BASE_URL}/api/marketplace/v3/supplies/{wb_supply_id}/order-ids"
        res = self.request("GET", url, timeout=(5, 10))
        return res.json().get("orderIds", []) if res.status_code == 200 else []

    def get_supply_orders(self, wb_supply_id: str) -> list[dict[str, Any]]:
        """GET /api/v3/supplies/{supplyId}/orders — Получение полных объектов заданий в поставке."""
        url = f"{self.BASE_URL}/api/v3/supplies/{wb_supply_id}/orders"
        res = self.request("GET", url, timeout=(5, 15))
        return res.json().get("orders", []) if res.status_code == 200 else []

    def deliver_supply(self, wb_supply_id: str) -> bool:
        """PATCH /api/v3/supplies/{supplyId}/deliver — Передача поставки в доставку."""
        url = f"{self.BASE_URL}/api/v3/supplies/{wb_supply_id}/deliver"
        res = self.request("PATCH", url, timeout=(5, 10))
        return res.status_code in (200, 204)

    def get_supply_barcode(self, wb_supply_id: str, barcode_type: str = "png") -> dict[str, Any] | None:
        """GET /api/v3/supplies/{supplyId}/barcode — Официальный QR-код закрытой поставки от WB."""
        url = f"{self.BASE_URL}/api/v3/supplies/{wb_supply_id}/barcode"
        res = self.request("GET", url, params={"type": barcode_type}, timeout=(5, 10))
        return res.json() if res.status_code == 200 else None