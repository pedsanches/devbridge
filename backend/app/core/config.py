"""
Application Settings.

Uses Pydantic Settings to load configuration from environment variables.
All settings are validated at startup.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ============================================================
    # Application
    # ============================================================
    PROJECT_NAME: str = "DevBridge"
    VERSION: str = "0.1.0"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"

    # ============================================================
    # API
    # ============================================================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = Field(default=["http://localhost:3000"])

    # ============================================================
    # Database
    # ============================================================
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql://devbridge:devbridge@localhost:5432/devbridge"
    )
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # ============================================================
    # Redis
    # ============================================================
    REDIS_URL: RedisDsn = Field(default="redis://localhost:6379/0")
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ============================================================
    # Vector Database (Qdrant)
    # ============================================================
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_COLLECTION: str = "devbridge"

    # ============================================================
    # AI / LLM
    # ============================================================
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"

    # ============================================================
    # GitHub
    # ============================================================
    GITHUB_APP_ID: str = ""
    GITHUB_APP_PRIVATE_KEY_PATH: str = "./secrets/github-app.pem"
    GITHUB_WEBHOOK_SECRET: str = ""
    GITHUB_TOKEN: str = ""

    # ============================================================
    # Slack
    # ============================================================
    SLACK_BOT_TOKEN: str = ""
    SLACK_SIGNING_SECRET: str = ""
    SLACK_CHANNEL_DEFAULT: str = "#devbridge-alerts"

    # ============================================================
    # Security
    # ============================================================
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30
    JWT_REFRESH_EXPIRATION_DAYS: int = 7

    # ============================================================
    # Privacy (Presidio)
    # ============================================================
    PRESIDIO_ANALYZER_URL: str = "http://localhost:5001"
    PRESIDIO_ANONYMIZER_URL: str = "http://localhost:5002"
    PRESIDIO_LANGUAGES: list[str] = Field(default=["pt", "en"])

    # ============================================================
    # Feature Flags
    # ============================================================
    ENABLE_SLACK_NOTIFICATIONS: bool = True
    ENABLE_DAILY_SUMMARY: bool = True
    ENABLE_RAG_CHAT: bool = True


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Returns:
        Settings instance (cached for performance).
    """
    return Settings()


# Global settings instance
settings = get_settings()
