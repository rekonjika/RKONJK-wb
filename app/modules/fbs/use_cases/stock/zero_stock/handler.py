# app/modules/fbs/use_cases/stock/zero_stock/handler.py

from sqlalchemy.orm import Session
from app.core.wb_client import WildberriesClient
from app.modules.catalog.domain.models.product import Product
from app.modules.fbs.domain.models.settings import FbsWarehouseProductSetting
from app.modules.fbs.use_cases.stock.zero_stock.dto import ZeroStockDTO


class ZeroStockHandler:
    def __init__(self, db: Session, client: WildberriesClient) -> None:
        self.db = db
        self.client = client

    def handle(self, dto: ZeroStockDTO) -> int:
        query = (
            self.db.query(FbsWarehouseProductSetting)
            .join(Product, FbsWarehouseProductSetting.barcode == Product.barcode)
            .filter(
                FbsWarehouseProductSetting.wb_warehouse_id == dto.warehouse_id,
                FbsWarehouseProductSetting.chrt_id.isnot(None)
            )
        )
        if dto.barcodes:
            query = query.filter(Product.barcode.in_(dto.barcodes))

        settings = query.all()
        if not settings:
            return 0

        payload = [{"chrtId": int(s.chrt_id), "amount": 0} for s in settings if s.chrt_id]
        zeroed_count = 0

        for i in range(0, len(payload), 1000):
            chunk = payload[i:i + 1000]
            chunk_settings = settings[i:i + 1000]
            if self.client.update_stocks(dto.warehouse_id, chunk):
                zeroed_count += len(chunk)
                for s in chunk_settings:
                    s.wb_stock = 0
                self.db.commit()

        return zeroed_count