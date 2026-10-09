# app/modules/fbs/presentation/stock_router.py

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, verify_permission
from app.core.wb_client import WildberriesClient
from app.models import User, FbsWarehouseProductSetting
from app.modules.fbs.use_cases.stock.push_delta.dto import PushStocksDTO
from app.modules.fbs.use_cases.stock.push_delta.handler import PushDeltaStocksHandler
from app.modules.fbs.use_cases.stock.zero_stock.dto import ZeroStockDTO
from app.modules.fbs.use_cases.stock.zero_stock.handler import ZeroStockHandler

router = APIRouter(prefix="/supply/fbs/stocks", tags=["fbs-stocks"])


def get_wb_client() -> WildberriesClient:
    if not settings.WB_API_KEY:
        raise HTTPException(status_code=400, detail="WB_API_KEY не настроен")
    return WildberriesClient(settings.WB_API_KEY)


class ToggleStockDTO(BaseModel):
    warehouse_id: int
    barcode: str
    is_active: bool


@router.post("/push")
def push_stocks(
    dto: PushStocksDTO,
    db: Session = Depends(get_db),
    client: WildberriesClient = Depends(get_wb_client),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    verify_permission(current_user, "stocks")
    count = PushDeltaStocksHandler(db, client).handle(dto)
    return {"status": "success", "message": f"Остатки выгружены ({count} SKU)!"}


@router.post("/zero")
def zero_stocks(
    dto: ZeroStockDTO,
    db: Session = Depends(get_db),
    client: WildberriesClient = Depends(get_wb_client),
    current_user: User = Depends(get_current_user)
) -> dict[str, Any]:
    verify_permission(current_user, "stocks")
    count = ZeroStockHandler(db, client).handle(dto)
    return {"status": "success", "message": f"Обнулено {count} позиций."}


@router.post("/toggle")
def toggle_stock(
    req: ToggleStockDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> dict[str, str]:
    verify_permission(current_user, "stocks")
    setting = db.query(FbsWarehouseProductSetting).filter(
        FbsWarehouseProductSetting.barcode == req.barcode,
        FbsWarehouseProductSetting.wb_warehouse_id == req.warehouse_id
    ).first()

    if setting:
        setting.is_active = req.is_active
    else:
        db.add(FbsWarehouseProductSetting(
            barcode=req.barcode,
            wb_warehouse_id=req.warehouse_id,
            is_active=req.is_active
        ))
    db.commit()
    return {"status": "success", "message": "Статус выгрузки сохранен"}