from app.core.config import Settings, resolve_secret
from unittest.mock import patch, MagicMock
import os
import sys


def test_config_defaults():
    with patch.dict(
        os.environ,
        {"SECRET_KEY": "dummy", "DATABASE_URL": "sqlite:///test.db"},
    ):
        s = Settings()
        assert s.PROJECT_NAME == "Carbon Horizon"


def test_environment_defaults_to_production(monkeypatch):
    assert Settings.model_fields["ENVIRONMENT"].default == "production"
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    from pydantic_settings import SettingsConfigDict

    class DefaultSettings(Settings):
        model_config = SettingsConfigDict(env_file=None)

    s = DefaultSettings(
        SECRET_KEY="b" * 32,
        DATABASE_URL="sqlite:///test.db",
        REDIS_URL="redis://localhost:6379/0",
        ALLOWED_ORIGINS=["https://carbonhorizon.app"],
        GEMINI_API_KEY=None,
    )
    assert s.ENVIRONMENT == "production"


def test_config_async_url():
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"}):
        s = Settings()
        assert "asyncpg" in s.async_database_url
    with patch.dict(
        os.environ, {"DATABASE_URL": "postgresql+psycopg2://test"}
    ):
        s = Settings()
        assert "asyncpg" in s.async_database_url


def test_config_render_postgres_url_normalization():
    with patch.dict(
        os.environ,
        {"DATABASE_URL": "postgres://user:pass@dpg-host:5432/carbonhorizon"},
    ):
        s = Settings()
        assert s.DATABASE_URL.startswith("postgresql://")
        assert "asyncpg" in s.async_database_url


def test_resolve_secret_from_env():
    with patch.dict(os.environ, {"MY_TEST_SECRET": "env-value"}):
        assert resolve_secret("MY_TEST_SECRET") == "env-value"


def test_resolve_secret_fallback_default():
    with patch.dict(os.environ, {}, clear=True):
        assert (
            resolve_secret("NON_EXISTENT_SECRET", default="fallback")
            == "fallback"
        )


def test_resolve_secret_from_secret_manager():
    mock_sm_client = MagicMock()
    mock_response = MagicMock()
    mock_response.payload.data = b"secret-from-gsm\n"
    mock_sm_client.access_secret_version.return_value = mock_response

    mock_sm_module = MagicMock()
    mock_sm_module.SecretManagerServiceClient.return_value = mock_sm_client

    with patch.dict(
        os.environ,
        {
            "GOOGLE_CLOUD_PROJECT": "test-gcp-project",
            "USE_SECRET_MANAGER": "true",
        },
        clear=True,
    ):
        with patch.dict(
            sys.modules, {"google.cloud.secretmanager": mock_sm_module}
        ):
            val = resolve_secret("TEST_SECRET")
            assert val == "secret-from-gsm"
            expected_name = (
                "projects/test-gcp-project/secrets/TEST_SECRET/versions/latest"
            )
            mock_sm_client.access_secret_version.assert_called_once_with(
                request={"name": expected_name}
            )
