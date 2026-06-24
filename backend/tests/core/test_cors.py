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
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"

def test_cors_unknown_origin_blocked():
    headers = {
        "Origin": "http://malicious.com",
        "Access-Control-Request-Method": "GET",
    }
    response = client.options("/api/v1/health", headers=headers)
    assert response.status_code == 400 or response.headers.get("access-control-allow-origin") is None

def test_production_cors_validation_fails_with_wildcard():
    # Production with wildcard should raise ValueError
    with pytest.raises(ValueError, match="Invalid CORS origin for production"):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=["*"],
            SECRET_KEY="supersecretproductionkeythats32chars",
            DATABASE_URL="sqlite:///./test.db",
            GEMINI_API_KEY="test-key"
        )

def test_production_cors_validation_fails_with_localhost():
    with pytest.raises(ValueError, match="Invalid CORS origin for production"):
        Settings(
            ENVIRONMENT="production",
            ALLOWED_ORIGINS=["http://localhost:3000"],
            SECRET_KEY="supersecretproductionkeythats32chars",
            DATABASE_URL="sqlite:///./test.db",
            GEMINI_API_KEY="test-key"
        )

def test_production_cors_validation_passes_with_valid_origins():
    settings = Settings(
        ENVIRONMENT="production",
        ALLOWED_ORIGINS=["https://my-frontend.com"],
        SECRET_KEY="supersecretproductionkeythats32chars",
        DATABASE_URL="sqlite:///./test.db",
        GEMINI_API_KEY="test-key"
    )
    assert settings.ALLOWED_ORIGINS == ["https://my-frontend.com"]

def test_cors_origins_parsing_from_string():
    settings = Settings(
        ALLOWED_ORIGINS="https://example.com, https://app.com"
    )
    assert "https://example.com" in settings.ALLOWED_ORIGINS
    assert "https://app.com" in settings.ALLOWED_ORIGINS
