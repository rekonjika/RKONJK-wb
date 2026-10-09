# app/modules/fbs/repository/supply_query.py

from typing import Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import case

from app.modules.catalog.domain.models.product import Product
from app.modules.fbs.domain.models.supply import FbsSupply


class SupplyQueryRepository:
    """Выборка поставок со всеми позициями и вычислением складов."""

    @classmethod
    def get_overview(cls, db: Session, status: str | None = None) -> list[dict[str, Any]]:
        supplies = cls._query_supplies(db, status)
        if not supplies:
            return []

        prod_map = cls._load_products_map(db, supplies)
        return [cls._serialize_supply(s, prod_map) for s in supplies]

    @staticmethod
    def _query_supplies(db: Session, status: str | None) -> list[FbsSupply]:
        query = db.query(FbsSupply).options(joinedload(FbsSupply.items))

        if status and status.strip().lower() not in ["all", "none", ""]:
            query = query.filter(FbsSupply.status == status.strip())
        else:
            query = query.filter(FbsSupply.status.in_(["in_assembly", "processing", "missing_on_wb", "delivered"]))

        return query.order_by(
            case((FbsSupply.status == "in_assembly", 0), else_=1),
            FbsSupply.created_at.desc(),
            FbsSupply.id.desc()
        ).all()

    @staticmethod
    def _load_products_map(db: Session, supplies: list[FbsSupply]) -> dict[str, Product]:
        barcodes = {str(i.barcode).strip() for s in supplies for i in s.items if i.barcode}
        if not barcodes:
            return {}
        products = db.query(Product).filter(Product.barcode.in_(list(barcodes))).all()
        return {str(p.barcode).strip(): p for p in products if p.barcode}

    @staticmethod
    def _serialize_supply(s: FbsSupply, prod_map: dict[str, Product]) -> dict[str, Any]:
        items_res = []
        for it in s.items:
            p = prod_map.get(str(it.barcode).strip())
            items_res.append({
                "task_id": str(it.task_id),
                "barcode": str(it.barcode or ""),
                "status": s.status,
                "article": p.article if p and p.article else (it.article or "—"),
                "brand": p.brand if p and p.brand else "",
                "title": p.title if p and p.title else (it.article or "Товар FBS"),
                "group_name": p.group_name if p and p.group_name else (it.group_name or "Общее"),
                "price": float(it.price or 0.0),
                "photo_url": p.photo_url if p else None,
                "part_a": it.part_a,
                "part_b": it.part_b
            })

        wh_name = s.warehouse_name
        if not wh_name or wh_name in ["—", "-", "None"]:
            wh_name = next((it.order.warehouse_name for it in s.items if it.order and it.order.warehouse_name), "Склад FBS")

        return {
            "id": str(s.id),
            "wb_supply_id": s.wb_supply_id,
            "shipment_name": s.shipment_name or f"Поставка {s.wb_supply_id}",
            "created_at": s.created_at.isoformat() if s.created_at else "",
            "qr_code": s.qr_code or f"WB-GI-{s.wb_supply_id.replace('WB-GI-', '')}",
            "status": s.status,
            "scan_date": s.scan_date.strftime("%d.%m.%Y %H:%M") if s.scan_date else None,
            "orders_count": len(s.items),
            "warehouse_name": wh_name,
            "is_mgt": s.is_mgt,
            "can_pvz": True,
            "items": items_res
        }