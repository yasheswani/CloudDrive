from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # =========================================================
    # DATABASE
    # =========================================================

    DATABASE_URL: str = "sqlite:///./drive.db"

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    JWT_SECRET: str = "change-this-in-production"

    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 14

    # =========================================================
    # STORAGE & VERCEL BLOB
    # =========================================================

    STORAGE_DIR: str = "./storage"

    MAX_UPLOAD_MB: int = 100

    BLOB_READ_WRITE_TOKEN: str = ""
    BLOB_STORE_ID: str = ""
    BLOB_WEBHOOK_PUBLIC_KEY: str = ""

    # =========================================================
    # FRONTEND
    # =========================================================

    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # =========================================================
    # SETTINGS
    # =========================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


import os

settings = Settings()

if settings.BLOB_READ_WRITE_TOKEN and not os.environ.get("BLOB_READ_WRITE_TOKEN"):
    os.environ["BLOB_READ_WRITE_TOKEN"] = settings.BLOB_READ_WRITE_TOKEN
