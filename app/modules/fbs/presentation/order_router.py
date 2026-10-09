# app/modules/fbs/presentation/order_router.py

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db, SessionLocal
from app.core.dependencies import get_current_user, verify_permission
from app.core.wb_client import WildberriesClient
from app.models import User
from app.modules.fbs.repository.order_query import OrderQueryRepository
from app.modules.fbs.use_cases.order.new.handler import NewOrderHandler
from app.modules.fbs.use_cases.order.cancel.dto import CancelOrderDTO
from app.modules.fbs.use_cases.order.cancel.handler import CancelOrderHandler
from app.modules.fbs.use_cases.order.reconcile.handler import ReconcileOrdersHandler
from app.modules.fbs.use_cases.order.sticker.dto import FetchStickersDTO
from app.modules.fbs.use_cases.order.sticker.handler import FetchStickersHandler

router = APIRouter(prefix="/supply/fbs/orders", tags=["fbs-orders"])


def get_wb_client() -> WildberriesClient:
    if not settings.WB_API_KEY:
        raise HTTPException(status_code=400, detail="WB_API_KEY не задан в конфигурации")
    return WildberriesClient(settings.WB_API_KEY)


def _bg_reconcile(token: str, days: int) -> None:
    with SessionLocal() as db:
        ReconcileOrdersHandler(db, WildberriesClient(token)).handle(days_back=days)


@router.get("")
def get_orders_feed(
    status: str | None = Query(None),
    warehouse_id: int | None = Query(None),
    limit: int | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    verify_permission(current_user, "stocks")
    return OrderQueryRepository.get_feed(db, status=status, warehouse_id=warehouse_id, limit=limit)


@router.post("/stickers")
def get_stickers(
    dto: FetchStickersDTO,
    db: Session = Depends(get_db),
    client: WildberriesClient = Depends(get_wb_client),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    verify_permission(current_user, "stocks")
    return {"stickers": FetchStickersHandler(db, client).handle(dto)}


@router.post("/cancel")
def cancel_order(
    dto: CancelOrderDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    verify_permission(current_user, "stocks")
    if not CancelOrderHandler(db).handle(dto):
        raise HTTPException(status_code=400, detail="Не удалось отменить задание")
    return {"status": "success", "message": f"Задание {dto.task_id} отменено"}


@router.post("/sync")
def trigger_orders_sync(
    background_tasks: BackgroundTasks,
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    client: WildberriesClient = Depends(get_wb_client),
    current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    verify_permission(current_user, "stocks")
    raw_orders = client.get_new_orders()
    wh_map = {int(w["id"]): w.get("name", "Склад FBS") for w in client.get_warehouses()}
    new_count = NewOrderHandler(db).handle(raw_orders, wh_map)

    background_tasks.add_task(_bg_reconcile, settings.WB_API_KEY, days)
    return {"status": "success", "message": f"Сбор выполнен (+{new_count} новых). Фоновый синк запущен!"}