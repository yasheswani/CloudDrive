from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # =========================================================
    # DATABASE
    # =========================================================

    # Local development default.
    # Vercel overrides this with DATABASE_URL.
    DATABASE_URL: str = "sqlite:///./drive.db"

    # =========================================================
    # AUTHENTICATION
    # =========================================================

    # Vercel must provide a real JWT_SECRET environment variable.
    JWT_SECRET: str = "CloudDrive-2026-JWT-Secret-9f8a7c6d5e4b3a2x1"

    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 14

    # =========================================================
    # STORAGE
    # =========================================================

    # Used for local development only.
    # We will later replace this with Supabase Storage.
    STORAGE_DIR: str = "./storage"

    MAX_UPLOAD_MB: int = 100

    # =========================================================
    # FRONTEND
    # =========================================================

    # Local development default.
    # Vercel overrides this with FRONTEND_ORIGIN.
    FRONTEND_ORIGIN: str = "https://cloud-drive-lilac.vercel.app/"

    # =========================================================
    # PYDANTIC SETTINGS
    # =========================================================

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
