import os
import pytest
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from app.core.config import settings

# Candidate URLs for test database setup
CANDIDATE_URLS = [
    os.getenv("POSTGRES_DEFAULT_URL"),
    "postgresql://carbon_user:changeme_use_strong_password@localhost:5432/carbonhorizon",
    "postgresql://postgres:password@localhost:5432/postgres",
]

def _get_working_engine():
    for url in CANDIDATE_URLS:
        if not url:
            continue
        try:
            engine = create_engine(url, isolation_level="AUTOCOMMIT")
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return engine, url
        except Exception:
            continue
    return None, None

@pytest.fixture(scope="module")
def setup_test_db():
    engine, url = _get_working_engine()
    if not engine:
        pytest.skip("PostgreSQL service not reachable with known test credentials")

    test_db_name = "carbonhorizon_test_migrations"
    with engine.connect() as conn:
        try:
            conn.execute(text(f"CREATE DATABASE {test_db_name}"))
        except Exception:
            pass

    # Build the test database URL based on the working connection
    base_url = url.rsplit("/", 1)[0]
    test_db_url = f"{base_url}/{test_db_name}"

    yield test_db_url

    with engine.connect() as conn:
        try:
            conn.execute(text(f"DROP DATABASE {test_db_name} WITH (FORCE)"))
        except Exception:
            pass

@pytest.fixture(scope="module")
def alembic_config(setup_test_db):
    """Create Alembic config pointing to the test DB."""
    test_db_url = setup_test_db
    original_url = settings.DATABASE_URL
    settings.DATABASE_URL = test_db_url

    alembic_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "alembic")
    alembic_ini_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "alembic.ini")

    config = Config(alembic_ini_path)
    config.set_main_option("script_location", alembic_dir)
    config.set_main_option("sqlalchemy.url", test_db_url)

    yield config

    settings.DATABASE_URL = original_url

def test_migrations_up_and_down(alembic_config):
    """
    Test that Alembic can cleanly upgrade to head and downgrade to base
    on a pristine PostgreSQL database.
    """
    command.upgrade(alembic_config, "head")
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
