"""
Alembic environment configuration for Carbon Horizon.

Supports:
  • Offline mode  — generates SQL scripts without a live DB connection
  • Online mode   — runs migrations against a live sync connection
DATABASE_URL is read from Settings (which reads .env).

Run migrations:
  alembic upgrade head          # apply all pending migrations
  alembic downgrade -1          # roll back one migration
  alembic revision --autogenerate -m "describe change"
"""
from __future__ import annotations

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, text
from sqlalchemy import create_engine

from alembic import context

# ── Ensure backend root is on sys.path ────────────────────────────────────
# Works whether alembic is run from /backend or from project root.
_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(_HERE)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

# ── App imports ────────────────────────────────────────────────────────────
from app.core.config import settings                    # reads .env
import app.models                                       # registers all 12 ORM models # noqa: F401
from app.db.base import Base                            # shared DeclarativeBase

# ── Alembic config object ──────────────────────────────────────────────────
config = context.config

# Override sqlalchemy.url in alembic.ini with the value from Settings.
# This is the single source of truth — .env → Settings → Alembic.
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set up loggers from alembic.ini [loggers] section.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ── Target metadata ────────────────────────────────────────────────────────
# Alembic uses this to diff the ORM schema against the live DB schema.
target_metadata = Base.metadata

# ── Dialect helpers ────────────────────────────────────────────────────────

def _migration_context_kwargs() -> dict:
    """
    Return context.configure() kwargs appropriate for PostgreSQL.
    """
    kwargs: dict = {
        "target_metadata": target_metadata,
        "compare_type": True,           # detect column type changes
        "compare_server_default": True, # detect server default changes
        "include_schemas": False,
    }
    return kwargs


# ── Offline migration ──────────────────────────────────────────────────────

def run_migrations_offline() -> None:
    """
    Generate SQL migration scripts without a live DB connection.

    Useful for reviewing DDL before applying, or for environments where
    direct DB access is restricted.

    Usage:
        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_migration_context_kwargs(),
    )
    with context.begin_transaction():
        context.run_migrations()


# ── Online migration ───────────────────────────────────────────────────────

def run_migrations_online() -> None:
    """
    Run migrations against a live database using a synchronous connection.

    Alembic does not support async engines directly; we always use the sync
    DATABASE_URL here.  For PostgreSQL the sync driver is psycopg2;
    for SQLite no extra driver is required.

    The async application engine (asyncpg / aiosqlite) is separate and used
    only by FastAPI request handlers.
    """
    url = config.get_main_option("sqlalchemy.url")

    # Build a sync engine scoped to this migration run (NullPool prevents
    # connection leaks when running multiple `alembic upgrade` calls).
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            **_migration_context_kwargs(),
        )
        with context.begin_transaction():
            context.run_migrations()


# ── Entrypoint ─────────────────────────────────────────────────────────────

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
