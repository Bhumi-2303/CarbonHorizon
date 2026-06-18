import pytest
import anyio
from main import startup_event
from app.core.config import settings

def test_startup_production_empty_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", "")
    with pytest.raises(ValueError, match="SECRET_KEY must be provided and cannot be a default value in production"):
        anyio.run(startup_event)

def test_startup_production_default_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", "change-me-in-production-use-32-char-minimum")
    with pytest.raises(ValueError, match="SECRET_KEY must be provided and cannot be a default value in production"):
        anyio.run(startup_event)

def test_startup_production_another_default_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", "change-me-use-a-32-char-random-hex-string")
    with pytest.raises(ValueError, match="SECRET_KEY must be provided and cannot be a default value in production"):
        anyio.run(startup_event)

def test_startup_production_valid_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", "some-secure-valid-key-here-1234567890")
    # Should not raise exception
    anyio.run(startup_event)

def test_startup_development_default_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "SECRET_KEY", "change-me-in-production-use-32-char-minimum")
    # Should not raise exception because it's not production
    anyio.run(startup_event)
