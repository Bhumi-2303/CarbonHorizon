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

from typing import List, Optional
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
    # Default: SQLite for zero-config local development.
    # Override in .env for PostgreSQL (staging / production).
    DATABASE_URL: str = "sqlite:///./carbonhorizon.db"

    # Async URL is derived from DATABASE_URL automatically if not set.
    # Supported substitutions:
    #   sqlite              → sqlite+aiosqlite
    #   postgresql          → postgresql+asyncpg
    #   postgresql+psycopg2 → postgresql+asyncpg
    ASYNC_DATABASE_URL: Optional[str] = None

    @property
    def async_database_url(self) -> str:
        """Return the async-compatible database URL."""
        if self.ASYNC_DATABASE_URL:
            return self.ASYNC_DATABASE_URL
        url = self.DATABASE_URL
        if url.startswith("sqlite:"):
            return url.replace("sqlite:", "sqlite+aiosqlite:", 1)
        if url.startswith("postgresql+psycopg2:"):
            return url.replace("postgresql+psycopg2:", "postgresql+asyncpg:", 1)
        if url.startswith("postgresql:"):
            return url.replace("postgresql:", "postgresql+asyncpg:", 1)
        return url  # already async-prefixed or unknown driver

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")

    @property
    def is_postgres(self) -> bool:
        return "postgresql" in self.DATABASE_URL

    # ── JWT / Auth ──────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-32-char-minimum"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]


settings = Settings()
