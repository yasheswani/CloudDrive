from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./drive.db"
    JWT_SECRET: str = "change-this-in-production"
    ACCESS_TOKEN_MINUTES: int = 30
    REFRESH_TOKEN_DAYS: int = 14
    STORAGE_DIR: str = "./storage"
    MAX_UPLOAD_MB: int = 100
    FRONTEND_ORIGIN: str = "http://localhost:5173"
    class Config:
        env_file = ".env"

settings = Settings()
