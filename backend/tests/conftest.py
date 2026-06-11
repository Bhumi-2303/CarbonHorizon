"""
conftest.py — shared pytest fixtures for Carbon Horizon auth tests.

Fixture hierarchy
-----------------
engine          per-session temporary SQLite file, tables created once
db_session      per-test transactional session, rolled back after every test
client          FastAPI TestClient wired to the same test DB
make_user       helper that creates a persisted User in the test DB
test_user       a single active User (email: testuser@example.com)
auth_headers    Authorization headers for test_user

Database strategy
-----------------
We use a temporary on-disk SQLite file (created fresh for each test SESSION)
rather than `:memory:` + StaticPool, because StaticPool reuses the same
underlying connection across process restarts which causes "index already
exists" errors on the second test run. The temp file is deleted after the
session via tmp_path_factory.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.security import (
    create_access_token,
    get_db,
    hash_password,
)
from app.db.base import Base
from app.models.user import User  # noqa: F401 — triggers model registration

# Import every model so all tables exist in Base.metadata before create_all
import app.models  # noqa: F401


# ---------------------------------------------------------------------------
# Database engine — fresh temp-file SQLite per test session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def engine(tmp_path_factory: pytest.TempPathFactory):
    """
    Create a fresh on-disk SQLite test database for the session.

    Using a real file (not :memory: + StaticPool) avoids the "index already
    exists" error that occurs when StaticPool reuses a connection that holds
    tables from a previous test run inside the same OS process.

    The file lives in a pytest-managed temp dir and is cleaned up automatically.
    """
    db_path = tmp_path_factory.mktemp("testdb") / "test_carbonhorizon.db"
    db_url  = f"sqlite:///{db_path}"

    _engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        echo=False,
    )
    Base.metadata.create_all(_engine)

    # Enable WAL mode for better concurrency in SQLite
    with _engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL"))

    yield _engine
    _engine.dispose()
    # pytest tmp_path_factory cleans up the directory automatically


@pytest.fixture(scope="session")
def session_factory(engine):
    """Return a sessionmaker bound to the test engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# Per-test DB session — auto-rolled back
# ---------------------------------------------------------------------------

@pytest.fixture()
def db(session_factory) -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy Session that is automatically rolled back after each test.
    This ensures tests are fully isolated without needing to truncate tables.
    """
    session = session_factory()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ---------------------------------------------------------------------------
# FastAPI TestClient wired to the same test DB
# ---------------------------------------------------------------------------

@pytest.fixture()
def client(db: Session):
    """
    Return a FastAPI TestClient that uses the test DB session via
    dependency_overrides, ensuring integration tests hit the same
    database as unit tests.
    """
    from main import app

    def override_get_db():
        try:
            yield db
        finally:
            pass  # session lifecycle handled by the `db` fixture

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Factories / helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def make_user(db: Session):
    """
    Factory fixture that creates and persists a User in the test DB.

    Usage:
        user = make_user()                          # defaults
        user = make_user(email="x@example.com")     # override any field
        user = make_user(deleted=True)              # soft-deleted account
    """
    def _create(
        *,
        full_name: str = "Test User",
        email: str | None = None,
        password: str = "TestPass123!",
        age_group: str | None = "adult",
        lifestyle_type: str | None = "professional",
        city: str | None = "Mumbai",
        country: str | None = "India",
        email_verified: bool = False,
        deleted: bool = False,
    ) -> User:
        _email = email or f"user_{uuid.uuid4().hex[:8]}@example.com"
        user = User(
            id=uuid.uuid4(),
            full_name=full_name,
            email=_email,
            password_hash=hash_password(password),
            age_group=age_group,
            lifestyle_type=lifestyle_type,
            city=city,
            country=country,
            email_verified=email_verified,
        )
        if deleted:
            user.deleted_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    return _create


@pytest.fixture()
def test_user(make_user) -> User:
    """A single ready-to-use active user."""
    return make_user(email=f"testuser_{uuid.uuid4().hex[:6]}@example.com", password="GoodPass42!")


@pytest.fixture()
def auth_headers(test_user: User) -> dict[str, str]:
    """
    Return Authorization headers for test_user with a freshly minted access token.
    """
    token = create_access_token(subject=str(test_user.id))
    return {"Authorization": f"Bearer {token}"}
