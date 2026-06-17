import pytest
from app.core.config import Settings, settings
from unittest.mock import patch
import os

def test_config_defaults():
    with patch.dict(os.environ, {"SECRET_KEY": "dummy", "DATABASE_URL": "sqlite:///test.db"}):
        s = Settings()
        assert s.PROJECT_NAME == "Carbon Horizon"
        
def test_config_async_url():
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://test"}):
        s = Settings()
        assert "asyncpg" in s.async_database_url
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql+psycopg2://test"}):
        s = Settings()
        assert "asyncpg" in s.async_database_url
