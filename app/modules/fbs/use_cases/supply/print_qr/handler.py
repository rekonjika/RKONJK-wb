# app/modules/fbs/use_cases/supply/print_qr/handler.py

from typing import Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.core.wb_client import WildberriesClient
from app.modules.fbs.domain.models.supply import FbsSupply
from app.modules.fbs.use_cases.supply.print_qr.dto import SupplyBarcodeDTO


class PrintSupplyQrHandler:
    def __init__(self, db: Session, client: WildberriesClient) -> None:
        self.db = db
        self.client = client

    def handle(self, dto: SupplyBarcodeDTO) -> dict[str, Any]:
        supply = self.db.query(FbsSupply).filter(FbsSupply.id == dto.supply_id).first()
        if not supply or not supply.wb_supply_id:
            raise HTTPException(status_code=404, detail="Поставка не найдена в базе данных")

        wb_data = self.client.get_supply_barcode(supply.wb_supply_id, barcode_type=dto.type)
        if not wb_data or not wb_data.get("file"):
            raise HTTPException(
                status_code=400,
                detail=f"QR-код для поставки {supply.wb_supply_id} доступен только после передачи в доставку (deliver)."
            )

        return {
            "supply_id": supply.id,
            "wb_supply_id": supply.wb_supply_id,
            "barcode": wb_data.get("barcode", f"WB-GI-{supply.wb_supply_id}"),
            "file": wb_data.get("file"),
            "type": dto.type
        }