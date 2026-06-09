"""
Application configuration using Pydantic BaseSettings.
Environment variables are loaded from a .env file at the root.
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Project metadata
    PROJECT_NAME: str = "Carbon Horizon"
    VERSION: str = "0.1.0"

    # API prefix
    API_V1_STR: str = "/api/v1"

    # Database
    DATABASE_URL: str = "postgresql://postgres:password@localhost:5432/carbonhorizon"

    # JWT / Auth
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
