import pytest
import anyio
from main import startup_event
from app.core.config import settings


def test_startup_production_empty_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "SECRET_KEY", "")
    with pytest.raises(
        ValueError,
        match=(
            "SECRET_KEY must be provided and cannot be a default value "
            "in production"
        ),
    ):
        anyio.run(startup_event)


def test_startup_production_default_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "change-me-in-production-use-32-char-minimum"
    )
    with pytest.raises(
        ValueError,
        match=(
            "SECRET_KEY must be provided and cannot be a default value "
            "in production"
        ),
    ):
        anyio.run(startup_event)


def test_startup_production_another_default_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "change-me-use-a-32-char-random-hex-string"
    )
    with pytest.raises(
        ValueError,
        match=(
            "SECRET_KEY must be provided and cannot be a default value "
            "in production"
        ),
    ):
        anyio.run(startup_event)


def test_startup_production_valid_key(monkeypatch):
    from unittest.mock import AsyncMock

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "some-secure-valid-key-here-1234567890"
    )
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", ["https://carbonhorizon.app"])
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "re_test_secret_12345")
    monkeypatch.setattr("app.core.redis_client.init_redis", AsyncMock())
    # Should not raise exception
    anyio.run(startup_event)


def test_startup_production_refuses_stub_email_provider(monkeypatch):
    from unittest.mock import AsyncMock

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "some-secure-valid-key-here-1234567890"
    )
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", ["https://carbonhorizon.app"])
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "stub")
    monkeypatch.setattr("app.core.redis_client.init_redis", AsyncMock())

    with pytest.raises(
        ValueError,
        match="EMAIL_PROVIDER cannot be 'stub' or 'console' in production",
    ):
        anyio.run(startup_event)


def test_startup_production_refuses_console_email_provider(monkeypatch):
    from unittest.mock import AsyncMock

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "some-secure-valid-key-here-1234567890"
    )
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", ["https://carbonhorizon.app"])
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "console")
    monkeypatch.setattr("app.core.redis_client.init_redis", AsyncMock())

    with pytest.raises(
        ValueError,
        match="EMAIL_PROVIDER cannot be 'stub' or 'console' in production",
    ):
        anyio.run(startup_event)


def test_startup_production_resend_missing_api_key(monkeypatch):
    from unittest.mock import AsyncMock

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "some-secure-valid-key-here-1234567890"
    )
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", ["https://carbonhorizon.app"])
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "resend")
    monkeypatch.setattr(settings, "RESEND_API_KEY", "")
    monkeypatch.setattr("app.core.redis_client.init_redis", AsyncMock())

    with pytest.raises(
        ValueError,
        match="RESEND_API_KEY secret must be configured in production",
    ):
        anyio.run(startup_event)


def test_startup_production_smtp_missing_password(monkeypatch):
    from unittest.mock import AsyncMock

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "some-secure-valid-key-here-1234567890"
    )
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", ["https://carbonhorizon.app"])
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.resend.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "")
    monkeypatch.setattr("app.core.redis_client.init_redis", AsyncMock())

    with pytest.raises(
        ValueError,
        match="SMTP_HOST and SMTP_PASSWORD secret must be configured in production",
    ):
        anyio.run(startup_event)


def test_startup_production_smtp_valid(monkeypatch):
    from unittest.mock import AsyncMock

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "some-secure-valid-key-here-1234567890"
    )
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", ["https://carbonhorizon.app"])
    monkeypatch.setattr(settings, "EMAIL_PROVIDER", "smtp")
    monkeypatch.setattr(settings, "SMTP_HOST", "smtp.resend.com")
    monkeypatch.setattr(settings, "SMTP_PASSWORD", "smtp_secret_pass")
    monkeypatch.setattr("app.core.redis_client.init_redis", AsyncMock())

    # Should not raise exception
    anyio.run(startup_event)


def test_startup_production_refuses_localhost_allowed_origins(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "some-secure-valid-key-here-1234567890"
    )
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", ["http://localhost:3000"])
    with pytest.raises(
        ValueError,
        match="Insecure origin 'http://localhost:3000' is not permitted",
    ):
        anyio.run(startup_event)


def test_startup_production_refuses_empty_allowed_origins(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "some-secure-valid-key-here-1234567890"
    )
    monkeypatch.setattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setattr(settings, "ALLOWED_ORIGINS", [])
    with pytest.raises(
        ValueError,
        match="ALLOWED_ORIGINS must be configured and non-empty in production",
    ):
        anyio.run(startup_event)


def test_startup_production_unset_redis_url(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "some-secure-valid-key-here-1234567890"
    )
    monkeypatch.setattr(settings, "REDIS_URL", None)
    with pytest.raises(
        ValueError,
        match="REDIS_URL must be provided and cannot be empty in production",
    ):
        anyio.run(startup_event)


def test_startup_development_default_key(monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(
        settings, "SECRET_KEY", "change-me-in-production-use-32-char-minimum"
    )
    # Should not raise exception because it's not production
    anyio.run(startup_event)
