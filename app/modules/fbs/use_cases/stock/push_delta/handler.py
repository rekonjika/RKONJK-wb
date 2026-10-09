# app/modules/fbs/use_cases/stock/push_delta/handler.py

import math
import logging
from typing import Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.wb_client import WildberriesClient
from app.modules.catalog.domain.models.product import Product
from app.modules.fbs.domain.models.order import FbsOrder
from app.modules.fbs.domain.models.order_item import FbsOrderItem
from app.modules.fbs.domain.models.supply import FbsSupply
from app.modules.fbs.domain.models.settings import FbsWarehouseProductSetting
from app.modules.fbs.domain.types.order_status import FbsOrderStatus
from app.modules.fbs.domain.types.supply_status import FbsSupplyStatus
from app.modules.fbs.use_cases.stock.push_delta.dto import PushStocksDTO

logger = logging.getLogger("push_delta_stocks_handler")


class PushDeltaStocksHandler:
    def __init__(self, db: Session, client: WildberriesClient) -> None:
        self.db = db
        self.client = client

    def handle(self, dto: PushStocksDTO | None = None) -> int:
        target_wh_ids = self._get_target_warehouses(dto)
        if not target_wh_ids:
            return 0

        reserves = self._calculate_reserves()
        total_pushed = 0

        for wh_id in target_wh_ids:
            settings = (
                self.db.query(FbsWarehouseProductSetting, Product)
                .join(Product, FbsWarehouseProductSetting.barcode == Product.barcode)
                .filter(
                    FbsWarehouseProductSetting.wb_warehouse_id == wh_id,
                    FbsWarehouseProductSetting.is_active == True,
                    FbsWarehouseProductSetting.chrt_id.isnot(None)
                )
                .all()
            )

            payload, settings_to_update = self._prepare_delta_payload(settings, reserves)
            if not payload:
                continue

            total_pushed += self._send_chunks(wh_id, payload, settings_to_update)

        return total_pushed

    def _get_target_warehouses(self, dto: PushStocksDTO | None) -> list[int]:
        if dto and dto.warehouse_id:
            return [dto.warehouse_id]
        whs = self.client.get_warehouses()
        return [int(w["id"]) for w in whs if not w.get("isDeleting", False)]

    def _calculate_reserves(self) -> dict[str, int]:
        active_filter = (
            (FbsOrder.status == FbsOrderStatus.NEW.value) & (
                (FbsOrderItem.supply_id.is_(None)) | (FbsSupply.status == FbsSupplyStatus.IN_ASSEMBLY.value)
            )
        ) | (
            (FbsOrder.status == FbsOrderStatus.CONFIRM.value) & (FbsSupply.status == FbsSupplyStatus.IN_ASSEMBLY.value)
        )

        rows = (
            self.db.query(FbsOrderItem.barcode, func.count(FbsOrderItem.id))
            .join(FbsOrder, FbsOrderItem.order_id == FbsOrder.id)
            .outerjoin(FbsSupply, FbsOrderItem.supply_id == FbsSupply.id)
            .filter(active_filter, FbsOrderItem.barcode.isnot(None))
            .group_by(FbsOrderItem.barcode)
            .all()
        )
        return {b: cnt for b, cnt in rows if b}

    def _prepare_delta_payload(
        self,
        settings: list[tuple[FbsWarehouseProductSetting, Product]],
        reserves: dict[str, int]
    ) -> tuple[list[dict[str, Any]], list[tuple[FbsWarehouseProductSetting, int]]]:
        payload: list[dict[str, Any]] = []
        updates: list[tuple[FbsWarehouseProductSetting, int]] = []

        for s_obj, p_obj in settings:
            phys = p_obj.stock.physical_quantity if p_obj.stock else 0
            res = reserves.get(p_obj.barcode, 0)
            target = self._calculate_target_stock(phys - res, s_obj.safety_stock, s_obj.max_stock)

            if target != (s_obj.wb_stock or 0):
                payload.append({"chrtId": int(s_obj.chrt_id), "amount": target})
                updates.append((s_obj, target))

        return payload, updates

    @staticmethod
    def _calculate_target_stock(real_available: int, safety_stock: int, max_stock: int | None) -> int:
        if real_available <= 2:
            return 0

        buffer = safety_stock if safety_stock > 0 else (
            1 if real_available <= 15 else
            math.ceil(real_available * 0.10) if real_available <= 100 else
            math.ceil(real_available * 0.08) if real_available <= 500 else
            math.ceil(real_available * 0.05)
        )

        net = max(0, real_available - buffer)
        if net <= 0:
            return 0
        if max_stock and max_stock > 0:
            return min(net, max_stock)

        return (
            net if real_available <= 15 else
            math.floor(net * 0.80) if real_available <= 100 else
            math.floor(net * 0.60) if real_available <= 500 else
            min(1000, math.floor(net * 0.50))
        )

    def _send_chunks(
        self,
        wh_id: int,
        payload: list[dict[str, Any]],
        updates: list[tuple[FbsWarehouseProductSetting, int]]
    ) -> int:
        pushed = 0
        for i in range(0, len(payload), 1000):
            chunk = payload[i:i + 1000]
            chunk_updates = updates[i:i + 1000]
            if self.client.update_stocks(wh_id, chunk):
                pushed += len(chunk)
                for s_obj, amt in chunk_updates:
                    s_obj.wb_stock = amt
                self.db.commit()
        return pushed