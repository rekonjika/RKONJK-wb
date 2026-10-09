# app/main.py

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models import User

# Подключение модулей
from app.routers.auth import router as auth_router
from app.modules.warehouse.presentation.warehouse_router import router as warehouse_router
from app.modules.fbs.presentation.order_router import router as fbs_orders_router
from app.modules.fbs.presentation.supply_router import router as fbs_supplies_router
from app.modules.fbs.presentation.stock_router import router as fbs_stocks_router
from app.modules.fbs.presentation.fbs_base_router import router as fbs_base_router

logger = logging.getLogger("rknjik_wb")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Инициализация БД и первого админа при старте контейнера."""
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(
                username="admin",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True
            ))
            db.commit()
            logger.info("[Startup] Дефолтный администратор создан: admin / admin123")

    logger.info(f"[Startup] {settings.APP_NAME} успешно запущен на порту {settings.PORT}!")
    yield
    logger.info("[Shutdown] Остановка сервиса.")


app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Регистрация чистых роутеров
app.include_router(auth_router)
app.include_router(warehouse_router)
app.include_router(fbs_orders_router)
app.include_router(fbs_supplies_router)
app.include_router(fbs_stocks_router)
app.include_router(fbs_base_router)


@app.get("/health", tags=["system"])
def health_check() -> dict[str, str]:
    return {"status": "ok", "app": settings.APP_NAME}