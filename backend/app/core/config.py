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

import os
import secrets
from dotenv import load_dotenv

load_dotenv()
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
    DATABASE_URL: str = os.getenv("DATABASE_URL") or "postgresql://postgres:password@localhost:5432/carbonhorizon"

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
    SECRET_KEY: str = os.getenv("SECRET_KEY") or ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── CORS ────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://carbonhorizon-frontend-tvxxkekeuq-el.a.run.app",
    ]

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # ── External APIs ───────────────────────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")

    @model_validator(mode="after")
    def validate_secrets(self) -> "Settings":
        insecure_placeholders = [
            "",
            "password",
            "changeme",
            "secret",
            "change-me-in-production-use-32-char-minimum",
            "change-me-use-a-32-char-random-hex-string",
            "changeme_use_strong_password",
            "replace_with_openssl_rand_hex_32"
        ]
        
        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY in insecure_placeholders:
                raise ValueError("SECRET_KEY must be properly configured in production environment.")
            
            # Check for insecure database passwords
            if any(p in self.DATABASE_URL for p in ["postgres:password@", "postgres:changeme@"]):
                raise ValueError("DATABASE_URL contains an insecure default password in production.")
                
            if not self.GEMINI_API_KEY or self.GEMINI_API_KEY in ["", "your_gemini_api_key_here"]:
                 raise ValueError("GEMINI_API_KEY must be properly configured in production environment.")
        else:
            if not self.SECRET_KEY or self.SECRET_KEY in insecure_placeholders:
                import logging
                logging.warning("Using ephemeral SECRET_KEY. This is not safe for production.")
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
