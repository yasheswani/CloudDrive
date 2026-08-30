from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ---------------------------------------------------------
    # Database
    # ---------------------------------------------------------
    # Local development uses SQLite.
    # Vercel will override this using the DATABASE_URL
    # environment variable from Vercel.
    DATABASE_URL: str = "sqlite:///./drive.db"

    # ---------------------------------------------------------
    # Authentication
    # ---------------------------------------------------------
    # IMPORTANT:
    # Set a strong JWT_SECRET in Vercel Environment Variables.
    JWT_SECRET: str = "change-this-in-production"

    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 14

    # ---------------------------------------------------------
    # Local file storage
    # ---------------------------------------------------------
    # This is used for local development.
    # Later we will replace this with Supabase Storage.
    STORAGE_DIR: str = "./storage"

    MAX_UPLOAD_MB: int = 100

    # ---------------------------------------------------------
    # Frontend
    # ---------------------------------------------------------
    # Local development default.
    # Vercel will override this with FRONTEND_ORIGIN.
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    # ---------------------------------------------------------
    # Pydantic settings
    # ---------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
