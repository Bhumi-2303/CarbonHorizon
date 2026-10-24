"""
SQLAlchemy engine and session factory.

Provides:
  • sync  engine + SessionLocal   → used by Alembic and sync FastAPI deps
  • async engine + AsyncSession   → used by async FastAPI routes (future)

SQLite:
  • check_same_thread=False is required for SQLite + multi-threaded WSGI.
  • NullPool is used for SQLite to avoid connection sharing issues.

PostgreSQL:
  • pool_pre_ping=True detects stale connections.
  • pool_size / max_overflow tuned for typical web workloads.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings

# ---------------------------------------------------------------------------
# Sync engine (Alembic + sync FastAPI Depends)
# ---------------------------------------------------------------------------

if settings.DATABASE_URL.startswith("sqlite"):
    _engine_kwargs: dict = {
        "connect_args": {"check_same_thread": False},
    }
else:
    _engine_kwargs: dict = {
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 300,
        "poolclass": QueuePool,
    }

engine = create_engine(settings.DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ---------------------------------------------------------------------------
# Async engine + session (wired when async routes are implemented)
# ---------------------------------------------------------------------------


def get_async_engine():
    """Return an async SQLAlchemy engine."""
    from sqlalchemy.ext.asyncio import create_async_engine as _async_engine

    if settings.async_database_url.startswith("sqlite"):
        kwargs: dict = {
            "echo": settings.DEBUG,
            "connect_args": {"check_same_thread": False},
        }
    else:
        kwargs: dict = {
            "echo": settings.DEBUG,
            "pool_pre_ping": True,
            "pool_size": 10,
            "max_overflow": 20,
            "pool_recycle": 300,
        }
    return _async_engine(settings.async_database_url, **kwargs)


def get_async_session_factory():
    """Return an async session factory (lazy import)."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    return async_sessionmaker(
        bind=get_async_engine(),
        class_=AsyncSession,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )
