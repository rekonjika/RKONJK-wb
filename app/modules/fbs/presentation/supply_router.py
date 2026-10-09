# app/modules/fbs/presentation/supply_router.py

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, verify_permission
from app.core.wb_client import WildberriesClient
from app.models import User
from app.modules.fbs.repository.supply_query import SupplyQueryRepository
from app.modules.fbs.use_cases.supply.create.dto import CreateSupplyDTO
from app.modules.fbs.use_cases.supply.create.handler import CreateSupplyHandler
from app.modules.fbs.use_cases.supply.add_orders.dto import AddOrdersToSupplyDTO
from app.modules.fbs.use_cases.supply.add_orders.handler import AddOrdersToSupplyHandler
from app.modules.fbs.use_cases.supply.deliver.dto import DeliverSupplyDTO
from app.modules.fbs.use_cases.supply.deliver.handler import DeliverSupplyHandler
from app.modules.fbs.use_cases.supply.print_qr.dto import SupplyBarcodeDTO
from app.modules.fbs.use_cases.supply.print_qr.handler import PrintSupplyQrHandler

router = APIRouter(prefix="/supply/fbs/supplies", tags=["fbs-supplies"])


def get_wb_client() -> WildberriesClient:
    if not settings.WB_API_KEY:
        raise HTTPException(status_code=400, detail="WB_API_KEY не задан")
    return WildberriesClient(settings.WB_API_KEY)


@router.get("")
def get_supplies(
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> list[dict[str, Any]]:
    verify_permission(current_user, "stocks")
    return SupplyQueryRepository.get_overview(db, status=status)


@router.post("")
def create_supply(
    dto: CreateSupplyDTO,
    db: Session = Depends(get_db),
    client: WildberriesClient = Depends(get_wb_client),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    verify_permission(current_user, "create_supply")
    supply = CreateSupplyHandler(db, client).handle(dto)
    if not supply:
        raise HTTPException(status_code=400, detail="Не удалось создать поставку на WB")
    return {"status": "success", "supply_id": supply.id, "wb_supply_id": supply.wb_supply_id}


@router.post("/add-orders")
@router.patch("/add-orders")
def add_orders_to_supply(
    dto: AddOrdersToSupplyDTO,
    db: Session = Depends(get_db),
    client: WildberriesClient = Depends(get_wb_client),
    current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    verify_permission(current_user, "create_supply")
    if not AddOrdersToSupplyHandler(db, client).handle(dto):
        raise HTTPException(status_code=400, detail="Не удалось добавить заказы в поставку")
    return {"status": "success", "message": "Заказы успешно добавлены в поставку"}


@router.patch("/{supply_id}/deliver")
def deliver_supply(
    supply_id: int,
    db: Session = Depends(get_db),
    client: WildberriesClient = Depends(get_wb_client),
    current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    verify_permission(current_user, "create_supply")
    if not DeliverSupplyHandler(db, client).handle(DeliverSupplyDTO(supply_id=supply_id)):
        raise HTTPException(status_code=400, detail="Не удалось отгрузить поставку на WB")
    return {"status": "success", "message": "Поставка отгружена, остатки списаны"}


@router.get("/{supply_id}/barcode")
def get_supply_barcode(
    supply_id: int,
    type: str = Query("png", regex="^(png|svg|zplv|zplh)$"),
    db: Session = Depends(get_db),
    client: WildberriesClient = Depends(get_wb_client),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    verify_permission(current_user, "stocks")
    return PrintSupplyQrHandler(db, client).handle(SupplyBarcodeDTO(supply_id=supply_id, type=type))