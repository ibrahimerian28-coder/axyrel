"""Centralized application configuration for Axyrel backend.

Task 43: keep runtime configuration in one typed Settings object. Secrets and
environment-specific values are loaded from environment variables/.env and
must not be hard-coded in source code.
"""
from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed runtime configuration loaded from environment variables/.env."""

    app_name: str = Field(default="Axyrel", alias="AXYREL_APP_NAME")
    app_version: str = Field(default="1.0.0", alias="AXYREL_APP_VERSION")
    environment: str = Field(default="development", alias="AXYREL_ENV")
    api_prefix: str = Field(default="/api/v1", alias="AXYREL_API_PREFIX")

    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/axyrel",
        alias="DATABASE_URL",
    )
    secret_key: str = Field(
        default="change-me-in-production",
        alias="SECRET_KEY",
    )
    access_token_expire_minutes: int = Field(
        default=60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES",
        ge=1,
    )

    # Task 45: Streamlit -> FastAPI integration settings.
    ui_api_enabled: bool = Field(default=True, alias="AXYREL_UI_API_ENABLED")
    api_base_url: str = Field(default="http://127.0.0.1:8000", alias="AXYREL_API_BASE_URL")
    api_token: str = Field(default="", alias="AXYREL_API_TOKEN")
    # Deprecated compatibility setting. Task 46 derives tenant context from the authenticated user.
    company_id: str = Field(default="", alias="AXYREL_COMPANY_ID")
    api_timeout_seconds: int = Field(default=20, alias="AXYREL_API_TIMEOUT_SECONDS", ge=1)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def validate_production_security(self) -> None:
        """Reject insecure development defaults when running in production."""
        if self.environment.lower() == "production":
            if self.secret_key == "change-me-in-production":
                raise ValueError("SECRET_KEY must be changed in production.")
            if "localhost" in self.database_url:
                raise ValueError("DATABASE_URL must not point to localhost in production.")


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings instance."""
    return Settings()


settings = get_settings()
