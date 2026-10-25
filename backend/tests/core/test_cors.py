import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from main import app

client = TestClient(app)


def test_cors_allowed_origin():
    # Send a request with an allowed origin
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "X-Custom-Header",
    }
    # We can use OPTIONS to test CORS preflight
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 200
    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:3000"
    )
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_unknown_origin_blocked():
    headers = {
        "Origin": "http://malicious.com",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/v1/health", headers=headers)
    assert (
        response.status_code == 400
        or response.headers.get("access-control-allow-origin") is None
    )


def test_production_cors_validation_fails_with_wildcard():
    # Production with wildcard should raise ValueError
    with pytest.raises(ValueError, match="Invalid CORS origin for production"):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=["*"],
            SECRET_KEY="supersecretproductionkeythats32chars",
            DATABASE_URL="sqlite:///./test.db",
            GEMINI_API_KEY="test-key",
        )


def test_cors_validation_fails_with_wildcard_in_development():
    with pytest.raises(
        ValueError, match="Wildcard '\\*' CORS origin is not allowed"
    ):
        Settings(
            ENVIRONMENT="development",
            ALLOWED_ORIGINS=["*"],
            SECRET_KEY="supersecretproductionkeythats32chars",
            DATABASE_URL="sqlite:///./test.db",
        )


def test_production_cors_validation_fails_with_localhost():
    with pytest.raises(ValueError, match="Invalid CORS origin for production"):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=["http://localhost:3000"],
            SECRET_KEY="supersecretproductionkeythats32chars",
            DATABASE_URL="sqlite:///./test.db",
            GEMINI_API_KEY="test-key",
        )


def test_production_cors_validation_passes_with_valid_origins():
    settings = Settings(
        ENVIRONMENT="production",
        ALLOWED_ORIGINS=["https://my-frontend.com"],
        SECRET_KEY="supersecretproductionkeythats32chars",
        DATABASE_URL="sqlite:///./test.db",
        GEMINI_API_KEY="test-key",
        REDIS_URL="redis://localhost:6379/0",
    )
    assert settings.ALLOWED_ORIGINS == ["https://my-frontend.com"]


def test_cors_origins_parsing_from_string():
    settings = Settings(ALLOWED_ORIGINS="https://example.com, https://app.com")
    assert "https://example.com" in settings.ALLOWED_ORIGINS
    assert "https://app.com" in settings.ALLOWED_ORIGINS


def test_cors_origins_parsing_from_json_string():
    settings = Settings(
        ALLOWED_ORIGINS=(
            '["https://carbonhorizon.vercel.app", '
            '"https://preview.vercel.app"]'
        )
    )
    assert settings.ALLOWED_ORIGINS == [
        "https://carbonhorizon.vercel.app",
        "https://preview.vercel.app",
    ]


def test_production_cors_validation_fails_with_run_app():
    with pytest.raises(ValueError, match="Invalid CORS origin for production"):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=[
                "https://carbonhorizon-frontend-tvxxkekeuq-el.a.run.app"
            ],
            SECRET_KEY="supersecretproductionkeythats32chars",
            DATABASE_URL="sqlite:///./test.db",
            REDIS_URL="redis://localhost:6379/0",
        )


def test_database_url_normalization_and_async_derivation():
    # 1. SQLite URL
    sqlite_settings = Settings(DATABASE_URL="sqlite:///./test.db")
    assert sqlite_settings.DATABASE_URL == "sqlite:///./test.db"
    assert sqlite_settings.async_database_url == "sqlite:///./test.db"

    # 2. Local PostgreSQL URL
    local_pg = "postgresql://user:secret@localhost:5432/carbonhorizon"
    pg_settings = Settings(DATABASE_URL=local_pg)
    assert pg_settings.DATABASE_URL == local_pg
    assert (
        pg_settings.async_database_url
        == "postgresql+asyncpg://user:secret@localhost:5432/carbonhorizon"
    )

    # 3. Neon-style URL with postgres:// scheme and ?sslmode=require
    neon_url = (
        "postgres://neon_user:neon_pass@ep-cool-1234.us-east-2.aws.neon.tech/"
        "neondb?sslmode=require"
    )
    neon_settings = Settings(DATABASE_URL=neon_url)
    assert neon_settings.DATABASE_URL.startswith("postgresql://")
    assert "sslmode=require" in neon_settings.DATABASE_URL
    assert neon_settings.async_database_url.startswith("postgresql+asyncpg://")


def test_production_settings_validation():
    # Insecure secret key fails
    with pytest.raises(
        ValueError, match="SECRET_KEY must be properly configured"
    ):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=["https://carbonhorizon.vercel.app"],
            SECRET_KEY="changeme_use_strong_password",
            DATABASE_URL=(
                "postgresql://user:pass@ep-test.neon.tech/dbname"
                "?sslmode=require"
            ),
            REDIS_URL="redis://localhost:6379/0",
        )

    # Insecure default DB password fails
    with pytest.raises(
        ValueError,
        match="DATABASE_URL contains an insecure default password",
    ):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=["https://carbonhorizon.vercel.app"],
            SECRET_KEY="supersecretproductionkeythats32chars",
            DATABASE_URL=(
                "postgresql://postgres:password@localhost:5432/carbonhorizon"
            ),
            REDIS_URL="redis://localhost:6379/0",
        )

    # Missing REDIS_URL in production fails
    with pytest.raises(
        ValueError, match="REDIS_URL must be set in production"
    ):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=["https://carbonhorizon.vercel.app"],
            SECRET_KEY="supersecretproductionkeythats32chars",
            DATABASE_URL=(
                "postgresql://user:realpassword@ep-test.neon.tech/dbname"
                "?sslmode=require"
            ),
            REDIS_URL="",
        )

    # Missing optional GEMINI_API_KEY does NOT block startup in production
    valid_prod = Settings(
        ENVIRONMENT="production",
        ALLOWED_ORIGINS=["https://carbonhorizon.vercel.app"],
        SECRET_KEY="supersecretproductionkeythats32chars",
        DATABASE_URL=(
            "postgresql://user:realpassword@ep-test.neon.tech/dbname"
            "?sslmode=require"
        ),
        REDIS_URL="redis://localhost:6379/0",
        GEMINI_API_KEY="",
    )
    assert valid_prod.ENVIRONMENT == "production"
    assert valid_prod.GEMINI_API_KEY == ""

    # Placeholder GEMINI_API_KEY in production fails
    with pytest.raises(
        ValueError, match="GEMINI_API_KEY contains an invalid placeholder"
    ):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=["https://carbonhorizon.vercel.app"],
            SECRET_KEY="supersecretproductionkeythats32chars",
            DATABASE_URL=(
                "postgresql://user:realpassword@ep-test.neon.tech/dbname"
                "?sslmode=require"
            ),
            REDIS_URL="redis://localhost:6379/0",
            GEMINI_API_KEY="your_gemini_api_key_here",
        )
