"""
Application configuration using Pydantic BaseSettings.

DATABASE_URL switching:
  • Dev  (default) → SQLite:    sqlite:///./carbonhorizon.db
  • Prod            → Postgres:  postgresql+psycopg2://user:pass@host/db
                               or postgresql+asyncpg://...  (async routes)

Set DATABASE_URL in .env to override.
ASYNC_DATABASE_URL is derived automatically from DATABASE_URL when not set.
"""
from __future__ import annotations

import secrets
from typing import List, Optional, Any, Union

from pydantic import model_validator, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Project metadata ────────────────────────────────────────────────────
    PROJECT_NAME: str = "Carbon Horizon"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # ── Environment ─────────────────────────────────────────────────────────
    ENVIRONMENT: str = "development"       # development | staging | production
    DEBUG: bool = True

    # ── Database ────────────────────────────────────────────────────────────
    # PostgreSQL configuration
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/carbonhorizon"

    # Async URL is derived from DATABASE_URL automatically if not set.
    ASYNC_DATABASE_URL: Optional[str] = None

    @property
    def async_database_url(self) -> str:
        """Return the async-compatible database URL."""
        if self.ASYNC_DATABASE_URL:
            return self.ASYNC_DATABASE_URL
        url = self.DATABASE_URL
        if url.startswith("postgresql+psycopg2:"):
            return url.replace("postgresql+psycopg2:", "postgresql+asyncpg:", 1)
        if url.startswith("postgresql:"):
            return url.replace("postgresql:", "postgresql+asyncpg:", 1)
        return url

    # ── JWT / Auth ──────────────────────────────────────────────────────────
    SECRET_KEY: str = ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://carbon-horizon.vercel.app",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # ── External APIs ───────────────────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = None

    @model_validator(mode="after")
    def assemble_secret_key(self) -> "Settings":
        default_keys = [
            "change-me-in-production-use-32-char-minimum",
            "change-me-use-a-32-char-random-hex-string"
        ]
        if self.ENVIRONMENT == "production":
            if not self.SECRET_KEY or self.SECRET_KEY in default_keys:
                self.SECRET_KEY = ""
        else:
            if not self.SECRET_KEY or self.SECRET_KEY in default_keys:
                self.SECRET_KEY = secrets.token_hex(32)
        return self

    @model_validator(mode="after")
    def validate_production_cors(self) -> "Settings":
        if self.ENVIRONMENT == "production":
            for origin in self.ALLOWED_ORIGINS:
                if origin == "*" or "localhost" in origin or "127.0.0.1" in origin:
                    raise ValueError(f"Invalid CORS origin for production: {origin}")
            if not self.ALLOWED_ORIGINS:
                raise ValueError("ALLOWED_ORIGINS must be set in production")
        return self


settings = Settings()
