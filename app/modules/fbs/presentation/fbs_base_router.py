# app/modules/fbs/presentation/fbs_base_router.py

from typing import Any
from fastapi import APIRouter, Depends
from app.core.config import settings
from app.core.dependencies import get_current_user, verify_permission
from app.core.wb_client import WildberriesClient
from app.models import User

router = APIRouter(prefix="/supply/fbs", tags=["fbs-base"])


@router.get("/warehouses")
def get_fbs_warehouses(current_user: User = Depends(get_current_user)) -> list[dict[str, Any]]:
    """Прямой эндпоинт для фронтенда: GET /supply/fbs/warehouses."""
    verify_permission(current_user, "stocks")
    if not settings.WB_API_KEY:
        return []

    client = WildberriesClient(settings.WB_API_KEY)
    warehouses = client.get_warehouses()
    return [
        {
            "id": int(wh["id"]),
            "name": wh.get("name") or f"Склад #{wh['id']}",
            "cargoType": wh.get("cargoType", 1),
            "deliveryType": wh.get("deliveryType", 1)
        }
        for wh in warehouses if not wh.get("isDeleting", False)
    ]