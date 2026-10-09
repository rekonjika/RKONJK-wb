# app/core/config.py

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App Config
    APP_NAME: str = "RKNJIK-WB ERP"
    APP_ENV: str = "development"
    DEBUG: bool = False
    PORT: int = 8000

    # Security
    SECRET_KEY: str = "super_secret_jwt_key_change_in_production_1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 часа

    # Database & Redis
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/rknjik_wb"
    REDIS_URL: str = "redis://localhost:6379/0"

    # Wildberries API
    WB_API_KEY: str = ""
    WB_MARKETPLACE_URL: str = "https://marketplace-api.wildberries.ru"
    WB_CONTENT_URL: str = "https://content-api.wildberries.ru"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
