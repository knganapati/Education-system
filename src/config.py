import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./skillbridge.db")
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-me")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
    MONITORING_TOKEN_EXPIRE_HOURS: int = int(os.getenv("MONITORING_TOKEN_EXPIRE_HOURS", "1"))
    MONITORING_API_KEY: str = os.getenv("MONITORING_API_KEY", "sb-monitor-key-2025-secure")
    APP_ENV: str = os.getenv("APP_ENV", "development")

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


settings = Settings()
