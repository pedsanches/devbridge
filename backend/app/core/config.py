"""
Application Settings.

Uses Pydantic Settings to load configuration from environment variables.
All settings are validated at startup.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
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
    API_HOST: str = "0.0.0.0"  # nosec B104
    API_PORT: int = 8001
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ]
    )

    # ============================================================
    # Database
    # ============================================================
    DATABASE_URL: str = Field(default="postgresql://devbridge:devbridge@localhost:5433/devbridge")
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10

    # ============================================================
    # Redis
    # ============================================================
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
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
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

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
    # Security / Auth
    # ============================================================
    SECRET_KEY: str = "change-me-in-production"
    JWT_SECRET_KEY: str = "change-me-in-production-jwt-secret-256-bits"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_DAYS: int = 7
    MAGIC_LINK_EXPIRE_MINUTES: int = 15

    # ============================================================
    # Rate Limiting
    # ============================================================
    RATE_LIMIT_PER_MINUTE: int = 100
    WEBHOOK_RATE_LIMIT_PER_HOUR: int = 100

    # ============================================================
    # Email (Resend)
    # ============================================================
    RESEND_API_KEY: str = ""
    EMAIL_FROM: str = "DevBridge <noreply@devbridge.io>"
    FRONTEND_URL: str = "http://localhost:3001"

    # ============================================================
    # Privacy (Presidio)
    # ============================================================
    PRESIDIO_ANALYZER_URL: str = "http://localhost:5001"
    PRESIDIO_ANONYMIZER_URL: str = "http://localhost:5002"
    PRESIDIO_LANGUAGES: list[str] = Field(default=["en", "pt"])

    # ============================================================
    # Feature Flags
    # ============================================================
    ENABLE_SLACK_NOTIFICATIONS: bool = True
    ENABLE_DAILY_SUMMARY: bool = True
    ENABLE_RAG_CHAT: bool = True

    @model_validator(mode="after")
    def validate_required_settings(self) -> "Settings":
        """Validate required settings on startup."""
        if not self.API_PREFIX.startswith("/"):
            raise ValueError("API_PREFIX must start with '/'")

        if not self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS cannot be empty")

        if not self.PRESIDIO_ANALYZER_URL or not self.PRESIDIO_ANONYMIZER_URL:
            raise ValueError("Presidio endpoints must be configured")

        if self.ENVIRONMENT == "production":
            required = [
                "SECRET_KEY",
                "JWT_SECRET_KEY",
                "OPENAI_API_KEY",
                "GITHUB_WEBHOOK_SECRET",
            ]
            missing = [name for name in required if not getattr(self, name)]
            if missing:
                raise ValueError("Missing required settings for production: " + ", ".join(missing))

        return self


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
