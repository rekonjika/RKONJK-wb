# app/modules/fbs/use_cases/order/sticker/handler.py

import logging
from typing import Any
from sqlalchemy.orm import Session

from app.core.wb_client import WildberriesClient
from app.modules.fbs.domain.models.order_item import FbsOrderItem
from app.modules.fbs.domain.models.sticker import FbsOrderSticker
from app.modules.fbs.use_cases.order.sticker.dto import FetchStickersDTO

logger = logging.getLogger("stickers_handler")


class FetchStickersHandler:
    """Ленивая подгрузка стикеров с проверкой локальной таблицы FbsOrderSticker."""

    def __init__(self, db: Session, client: WildberriesClient) -> None:
        self.db = db
        self.client = client

    def handle(self, dto: FetchStickersDTO) -> list[dict[str, Any]]:
        clean_ids = [str(o).strip() for o in dto.orders if str(o).strip().isdigit()]
        if not clean_ids:
            return []

        stickers_map, missing_ids = self._load_from_cache(clean_ids)
        if missing_ids:
            self._fetch_and_cache_missing(missing_ids, dto, stickers_map)

        return [stickers_map[tid] for tid in clean_ids if tid in stickers_map]

    def _load_from_cache(self, task_ids: list[str]) -> tuple[dict[str, dict[str, Any]], list[str]]:
        items = self.db.query(FbsOrderItem).filter(FbsOrderItem.task_id.in_(task_ids)).all()
        stickers_map: dict[str, dict[str, Any]] = {}
        missing_ids: list[str] = []

        for item in items:
            if item.sticker and item.sticker.file_base64:
                stickers_map[item.task_id] = {
                    "orderId": int(item.task_id),
                    "partA": item.part_a,
                    "partB": item.part_b,
                    "barcode": item.barcode,
                    "file": item.sticker.file_base64
                }
            else:
                missing_ids.append(item.task_id)

        return stickers_map, missing_ids

    def _fetch_and_cache_missing(
        self,
        missing_ids: list[str],
        dto: FetchStickersDTO,
        stickers_map: dict[str, dict[str, Any]]
    ) -> None:
        for i in range(0, len(missing_ids), 100):
            chunk = [int(x) for x in missing_ids[i:i + 100]]
            try:
                for s in self.client.get_stickers(chunk, dto.type, dto.width, dto.height):
                    tid = str(s.get("orderId") or s.get("id"))
                    file_b64 = s.get("file")
                    if not file_b64:
                        continue

                    item = self.db.query(FbsOrderItem).filter(FbsOrderItem.task_id == tid).first()
                    if item:
                        item.part_a = s.get("partA")
                        item.part_b = s.get("partB")
                        item.sticker = FbsOrderSticker(
                            task_id=tid,
                            sticker_type=dto.type,
                            file_base64=file_b64
                        )

                    stickers_map[tid] = {
                        "orderId": int(tid),
                        "partA": s.get("partA"),
                        "partB": s.get("partB"),
                        "barcode": s.get("barcode"),
                        "file": file_b64
                    }
                self.db.commit()
            except Exception as exc:
                logger.error(f"[Stickers Fetch Error] {exc}")