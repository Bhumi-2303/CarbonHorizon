"""
Application configuration using Pydantic BaseSettings.

DATABASE_URL:
  • Default: PostgreSQL
    (postgresql://postgres:password@localhost:5432/carbonhorizon)
  • External (e.g. Neon):
    postgresql://user:pass@ep-xyz.region.aws.neon.tech/dbname?sslmode=require
  • Test / SQLite: sqlite:///./carbonhorizon.db

Set DATABASE_URL in .env or environment variables to override the default.
ASYNC_DATABASE_URL is derived automatically from DATABASE_URL when not set.
"""

from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, field_validator
from typing import List, Optional, Any
import json
import logging
import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(_BACKEND_DIR / ".env")
load_dotenv(_BACKEND_DIR.parent / ".env")
load_dotenv()

logger = logging.getLogger(__name__)


def resolve_secret(
    secret_name: str, default: Optional[str] = None
) -> Optional[str]:
    """
    Resolve configuration secrets in order:
    1. Environment variables (process env, Cloud Run secrets, or .env)
    2. Google Cloud Secret Manager (if project/USE_SECRET_MANAGER configured)
    3. Provided default fallback
    """
    val = os.getenv(secret_name)
    if val is not None and val != "":
        return val

    project_id = (
        os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT")
        or os.getenv("PROJECT_ID")
    )
    use_sm = os.getenv("USE_SECRET_MANAGER", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    if project_id and (use_sm or os.getenv("ENVIRONMENT") == "production"):
        try:
            from google.cloud import secretmanager

            client = secretmanager.SecretManagerServiceClient()
            name = (
                f"projects/{project_id}/secrets/{secret_name}/versions/latest"
            )
            response = client.access_secret_version(request={"name": name})
            payload = response.payload.data.decode("utf-8").strip()
            if payload:
                logger.info(
                    f"Loaded secret '{secret_name}' from Google Secret Manager"
                )
                return payload
        except ImportError:
            logger.debug(
                "google-cloud-secret-manager library not installed; "
                "skipping Secret Manager lookup"
            )
        except Exception as exc:
            logger.debug(
                f"Unable to load secret '{secret_name}' "
                f"from Google Secret Manager: {exc}"
            )

    return default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # ── Project metadata ────────────────────────────────────────────────────
    PROJECT_NAME: str = "Carbon Horizon"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # ── Environment ─────────────────────────────────────────────────────────
    ENVIRONMENT: str = "production"  # development | staging | production
    DEBUG: bool = False

    @property
    def is_production(self) -> bool:
        """Return True if running in production environment."""
        return self.ENVIRONMENT.lower() == "production"

    # ── Database ────────────────────────────────────────────────────────────
    # PostgreSQL configuration
    DATABASE_URL: str = (
        resolve_secret("DATABASE_URL")
        or "postgresql://postgres:password@localhost:5432/carbonhorizon"
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_url(cls, v: Any) -> Any:
        if isinstance(v, str) and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v

    # Async URL is derived from DATABASE_URL automatically if not set.
    ASYNC_DATABASE_URL: Optional[str] = None

    @property
    def async_database_url(self) -> str:
        """Return the async-compatible database URL."""
        if self.ASYNC_DATABASE_URL:
            return self.ASYNC_DATABASE_URL
        url = self.DATABASE_URL
        if url.startswith("postgresql+psycopg2:"):
            return url.replace(
                "postgresql+psycopg2:", "postgresql+asyncpg:", 1
            )
        if url.startswith("postgresql:"):
            return url.replace("postgresql:", "postgresql+asyncpg:", 1)
        return url

    # ── JWT / Auth ──────────────────────────────────────────────────────────
    SECRET_KEY: str = resolve_secret("SECRET_KEY") or ""
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Redis (Token Revocation) ────────────────────────────────────────────
    REDIS_URL: Optional[str] = None
    REDIS_FAIL_OPEN: bool = False  # default: fail closed (reject if down)

    # ── CORS ────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = [
        "https://carbonhorizon.app",
        "https://carbon-horizon.vercel.app",
    ]

    # ── Trusted Proxies & Client IP ─────────────────────────────────────────
    # In Cloud Run with Nginx frontend reverse proxy:
    # (Browser -> Frontend Nginx -> Backend Run.app),
    # there are 2 trusted proxy hops from the right (Backend GFE and Frontend Nginx).
    TRUSTED_PROXY_COUNT: int = 1
    DEBUG_CLIENT_IP: bool = False
    TRUSTED_PROXIES: List[str] = [
        "127.0.0.1/32",
        "::1/128",
        "10.0.0.0/8",
        "172.16.0.0/12",
        "192.168.0.0/16",
        "169.254.0.0/16",
    ]

    # ── Email Service Provider ──────────────────────────────────────────────
    EMAIL_PROVIDER: str = "console"  # "console" | "stub" | "resend" | "smtp"
    EMAIL_FROM: str = "security@carbonhorizon.app"
    RESEND_API_KEY: Optional[str] = resolve_secret("RESEND_API_KEY")
    SMTP_HOST: Optional[str] = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: Optional[str] = os.getenv("SMTP_USER")
    SMTP_PASSWORD: Optional[str] = resolve_secret("SMTP_PASSWORD")
    SMTP_USE_TLS: bool = os.getenv("SMTP_USE_TLS", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    @model_validator(mode="before")
    @classmethod
    def set_environment_defaults(cls, data: Any) -> Any:
        if isinstance(data, dict):
            env = (
                data.get("ENVIRONMENT")
                or os.getenv("ENVIRONMENT")
                or "production"
            )
            if "ALLOWED_ORIGINS" not in data and not os.getenv(
                "ALLOWED_ORIGINS"
            ):
                if env in ("development", "testing"):
                    data["ALLOWED_ORIGINS"] = [
                        "http://localhost:3000",
                        "http://localhost:5173",
                    ]
                else:
                    data["ALLOWED_ORIGINS"] = [
                        "https://carbonhorizon.app",
                        "https://carbon-horizon.vercel.app",
                    ]
        return data

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [
                            str(i).strip() for i in parsed if str(i).strip()
                        ]
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("TRUSTED_PROXIES", mode="before")
    @classmethod
    def assemble_trusted_proxies(cls, v: Any) -> Any:
        if isinstance(v, str):
            v_stripped = v.strip()
            if v_stripped.startswith("[") and v_stripped.endswith("]"):
                try:
                    parsed = json.loads(v_stripped)
                    if isinstance(parsed, list):
                        return [
                            str(i).strip() for i in parsed if str(i).strip()
                        ]
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    # ── External APIs & Bot Protection ─────────────────────────────────────
    GEMINI_API_KEY: Optional[str] = resolve_secret("GEMINI_API_KEY")
    TURNSTILE_SECRET_KEY: Optional[str] = resolve_secret(
        "TURNSTILE_SECRET_KEY"
    )

    @model_validator(mode="after")
    def validate_production_cors(self) -> "Settings":
        for origin in self.ALLOWED_ORIGINS:
            if origin == "*":
                if self.ENVIRONMENT == "production":
                    raise ValueError(
                        f"Invalid CORS origin for production: {origin}"
                    )
                raise ValueError(
                    "Wildcard '*' CORS origin is not allowed. "
                    "Specify exact frontend origin(s)."
                )
        if self.ENVIRONMENT == "production":
            for origin in self.ALLOWED_ORIGINS:
                if (
                    "localhost" in origin
                    or "127.0.0.1" in origin
                    or "run.app" in origin
                ):
                    raise ValueError(
                        f"Invalid CORS origin for production: {origin}"
                    )
            if not self.ALLOWED_ORIGINS:
                raise ValueError("ALLOWED_ORIGINS must be set in production")
        return self

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
            "replace_with_openssl_rand_hex_32",
        ]

        if self.ENVIRONMENT == "production":
            if self.SECRET_KEY in insecure_placeholders:
                raise ValueError(
                    "SECRET_KEY must be properly configured in "
                    "production environment."
                )

            # Check for empty or insecure database passwords
            if not self.DATABASE_URL:
                raise ValueError(
                    "DATABASE_URL must be configured in "
                    "production environment."
                )

            if any(
                p in self.DATABASE_URL
                for p in ["postgres:password@", "postgres:changeme@"]
            ):
                raise ValueError(
                    "DATABASE_URL contains an insecure default password "
                    "in production."
                )

            # Redis is required in production for token revocation
            if not self.REDIS_URL:
                raise ValueError(
                    "REDIS_URL must be set in production for token "
                    "revocation. Example: redis://redis:6379/0"
                )

            # Validate Gemini API key if provided
            if self.GEMINI_API_KEY:
                if (
                    self.GEMINI_API_KEY in insecure_placeholders
                    or self.GEMINI_API_KEY == "your_gemini_api_key_here"
                ):
                    raise ValueError(
                        "GEMINI_API_KEY contains an invalid placeholder in "
                        "production environment."
                    )
            else:
                logger.warning(
                    "GEMINI_API_KEY is not configured in production. "
                    "AI Coach chat functionality will be unavailable."
                )
        else:
            if not self.SECRET_KEY or self.SECRET_KEY in insecure_placeholders:
                logger.warning(
                    "Using ephemeral SECRET_KEY. This is not safe "
                    "for production."
                )
                self.SECRET_KEY = secrets.token_hex(32)
        return self


settings = Settings()
