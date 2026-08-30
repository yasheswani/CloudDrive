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
    # STORAGE
    # =========================================================

    STORAGE_DIR: str = "./storage"

    MAX_UPLOAD_MB: int = 100

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


settings = Settings()
