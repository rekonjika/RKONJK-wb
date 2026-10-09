# app/core/wb_client/content_api.py

from typing import Any
from app.core.wb_client.base import BaseWbClient


class ContentApi(BaseWbClient):
    """Методы Wildberries Content API v2 (Номенклатура, Карточки, Фотографии)."""

    BASE_URL = "https://content-api.wildberries.ru"

    def get_cards_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        """POST /content/v2/get/cards/list — Постраничное получение или поиск карточек."""
        url = f"{self.BASE_URL}/content/v2/get/cards/list?locale=ru"
        res = self.request("POST", url, json=payload, timeout=(5, 20))
        return res.json() if res.status_code == 200 else {}