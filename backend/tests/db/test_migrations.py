import os
import pytest
from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text

from app.core.config import settings

# This test requires a running PostgreSQL instance, which should be the case 
# as per our Docker Compose config.
# We'll create a temporary test database to avoid messing with the dev db.

TEST_DB_URL = "postgresql://postgres:password@localhost:5432/carbonhorizon_test_migrations"

@pytest.fixture(scope="module")
def setup_test_db():
    # Connect to default postgres db to create the test db
    default_url = "postgresql://postgres:password@localhost:5432/postgres"
    engine = create_engine(default_url, isolation_level="AUTOCOMMIT")
    
    with engine.connect() as conn:
        try:
            conn.execute(text("CREATE DATABASE carbonhorizon_test_migrations"))
        except Exception:
            pass # DB might already exist

    yield

    with engine.connect() as conn:
        try:
            conn.execute(text("DROP DATABASE carbonhorizon_test_migrations WITH (FORCE)"))
        except Exception:
            pass

@pytest.fixture(scope="module")
def alembic_config(setup_test_db):
    """Create Alembic config pointing to the test DB."""
    # Alembic relies on settings.DATABASE_URL
    original_url = settings.DATABASE_URL
    settings.DATABASE_URL = TEST_DB_URL
    
    alembic_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "alembic")
    alembic_ini_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "alembic.ini")
    
    config = Config(alembic_ini_path)
    config.set_main_option("script_location", alembic_dir)
    config.set_main_option("sqlalchemy.url", TEST_DB_URL)
    
    yield config
    
    # Restore
    settings.DATABASE_URL = original_url

def test_migrations_up_and_down(alembic_config):
    """
    Test that Alembic can cleanly upgrade to head and downgrade to base
    on a pristine PostgreSQL database.
    """
    # Upgrade to head
    command.upgrade(alembic_config, "head")
    
    # Downgrade to base
    command.downgrade(alembic_config, "base")
    
    # Upgrade back to head to leave it ready if needed
    command.upgrade(alembic_config, "head")
