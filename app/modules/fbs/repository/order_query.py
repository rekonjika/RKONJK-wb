# app/modules/fbs/repository/order_query.py

from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import Session, joinedload

from app.modules.catalog.domain.models.product import Product
from app.modules.fbs.domain.models.order import FbsOrder
from app.modules.fbs.domain.models.order_item import FbsOrderItem
from app.modules.fbs.domain.types.order_status import FbsOrderStatus


class OrderQueryRepository:
    """Выборка сборочных заданий для фронтенда с расчетом SLA и обогащением карточками."""

    @classmethod
    def get_feed(
        cls,
        db: Session,
        status: str | None = None,
        warehouse_id: int | None = None,
        limit: int | None = None
    ) -> list[dict[str, Any]]:
        orders = cls._query_orders(db, status, warehouse_id, limit)
        if not orders:
            return []

        prod_map = cls._load_products_map(db, orders)
        now = datetime.now(timezone.utc)

        return [cls._serialize_order(o, prod_map, now) for o in orders]

    @staticmethod
    def _query_orders(
        db: Session,
        status: str | None,
        warehouse_id: int | None,
        limit: int | None
    ) -> list[FbsOrder]:
        query = db.query(FbsOrder).options(joinedload(FbsOrder.items).joinedload(FbsOrderItem.product))

        if status and status.strip().lower() not in ["all", "none", ""]:
            query = query.filter(FbsOrder.status == status.strip())
        else:
            query = query.filter(FbsOrder.status.in_(FbsOrderStatus.active_statuses()))

        if warehouse_id:
            query = query.filter(FbsOrder.warehouse_id == warehouse_id)

        query = query.order_by(FbsOrder.sla_deadline.asc(), FbsOrder.created_at.desc())
        return query.limit(limit).all() if limit else query.all()

    @staticmethod
    def _load_products_map(db: Session, orders: list[FbsOrder]) -> dict[str, Product]:
        barcodes = {str(i.barcode).strip() for o in orders for i in o.items if i.barcode}
        if not barcodes:
            return {}
        products = db.query(Product).filter(Product.barcode.in_(list(barcodes))).all()
        return {str(p.barcode).strip(): p for p in products if p.barcode}

    @classmethod
    def _serialize_order(cls, o: FbsOrder, prod_map: dict[str, Product], now: datetime) -> dict[str, Any]:
        sla_hours = None
        if o.sla_deadline:
            deadline = o.sla_deadline if o.sla_deadline.tzinfo else o.sla_deadline.replace(tzinfo=timezone.utc)
            sla_hours = round((deadline - now).total_seconds() / 3600, 1)

        items_res = [cls._serialize_item(i, prod_map, o.status) for i in o.items]

        return {
            "id": o.id,
            "order_uid": o.order_uid,
            "status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else "",
            "sla_deadline": o.sla_deadline.isoformat() if o.sla_deadline else None,
            "sla_hours_left": sla_hours,
            "is_urgent": sla_hours is not None and sla_hours < 24,
            "warehouse_id": o.warehouse_id,
            "warehouse_name": o.warehouse_name or "Склад FBS",
            "city": o.city,
            "cargo_type": o.cargo_type or 1,
            "is_pvz_allowed": o.is_pvz_allowed,
            "is_b2b": o.is_b2b,
            "items_count": len(items_res),
            "items": items_res
        }

    @staticmethod
    def _serialize_item(i: FbsOrderItem, prod_map: dict[str, Product], order_status: str) -> dict[str, Any]:
        p = prod_map.get(str(i.barcode).strip()) or i.product
        return {
            "task_id": str(i.task_id),
            "rid": i.rid,
            "barcode": str(i.barcode or (p.barcode if p else "")),
            "article": (p.article if p and p.article and p.article != "—" else (i.article or "—")),
            "brand": (p.brand if p and p.brand else ""),
            "title": (p.title if p and p.title else (i.article or "Товар FBS")),
            "group_name": (p.group_name if p and p.group_name else (i.group_name or "Общее")),
            "price": float(i.price or 0.0),
            "photo_url": p.photo_url if p else None,
            "part_a": i.part_a,
            "part_b": i.part_b,
            "status": order_status
        }