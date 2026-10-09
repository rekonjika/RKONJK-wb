# app/core/database.py

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# Корректировка префикса Railway для SQLAlchemy
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url, pool_size=10, max_overflow=20, pool_recycle=1800, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей проекта (SQLAlchemy 2.0)."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency для получения сессии БД в эндпоинтах FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
