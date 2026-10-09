# app/models.py

from app.modules.catalog.domain.models.product import Product
from app.modules.inventory.domain.models.stock import WarehouseStock
from app.modules.inventory.domain.models.movement import StockMovement, StockMovementType
from app.modules.inventory.domain.models.import_log import WarehouseImportLog
from app.modules.auth.domain.models.user import User
from app.modules.fbs.domain.models.order import FbsOrder
from app.modules.fbs.domain.models.order_item import FbsOrderItem
from app.modules.fbs.domain.models.supply import FbsSupply
from app.modules.fbs.domain.models.sticker import FbsOrderSticker
from app.modules.fbs.domain.models.settings import FbsWarehouseProductSetting
from app.modules.fbo.domain.models.fbo import WarehouseTier, WbStock, Supply

# Алиас
OurWarehouse = Product

__all__ = [
    "Product",
    "WarehouseStock",
    "StockMovement",
    "StockMovementType",
    "WarehouseImportLog",
    "User",
    "FbsOrder",
    "FbsOrderItem",
    "FbsSupply",
    "FbsOrderSticker",
    "FbsWarehouseProductSetting",
    "WarehouseTier",
    "WbStock",
    "Supply",
    "OurWarehouse"
]