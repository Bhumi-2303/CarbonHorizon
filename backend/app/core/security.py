"""
app/core/security.py
====================
Cryptographic helpers AND the get_current_user FastAPI dependency.

This module is the single security entry point for Carbon Horizon.
Routers import directly from here:

    from app.core.security import get_current_user, get_current_active_user

Sections
--------
1. Password hashing   — bcrypt (direct, no passlib)
2. JWT helpers        — python-jose (create / decode)
3. FastAPI auth deps  — get_current_user, get_current_active_user, get_db

bcrypt note
-----------
passlib 1.7.4 is incompatible with bcrypt ≥ 4.0 on Python 3.14
(missing __about__ attribute; 72-byte probe crash).
We call bcrypt.hashpw / bcrypt.checkpw directly.
"""
from __future__ import annotations

import bcrypt
from datetime import datetime, timedelta, timezone
from typing import Any, Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal

# ---------------------------------------------------------------------------
# 1. Password hashing
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain* text password."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the bcrypt *hashed* password."""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


# ---------------------------------------------------------------------------
# 2. JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(
    subject: Any,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject:       The unique identifier to embed in `sub` (usually user UUID).
        expires_delta: Override the default TTL (settings.ACCESS_TOKEN_EXPIRE_MINUTES).

    Returns:
        Signed JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": str(subject), "exp": expire, "type": "access"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Any) -> str:
    """
    Create a signed JWT refresh token (TTL = settings.REFRESH_TOKEN_EXPIRE_DAYS).

    Args:
        subject: The unique identifier to embed in `sub` (usually user UUID).

    Returns:
        Signed JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    payload = {"sub": str(subject), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    Args:
        token: Signed JWT string.

    Returns:
        Decoded claims dict.

    Raises:
        jose.JWTError: If the token is expired, malformed, or has an invalid signature.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# ---------------------------------------------------------------------------
# 3. FastAPI dependencies
# ---------------------------------------------------------------------------

# HTTPBearer reads `Authorization: Bearer <token>` from the request header.
_bearer_scheme = HTTPBearer(auto_error=True)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency — yields a synchronous SQLAlchemy Session.

    Rolls back on any unhandled exception; always closes the session.

    Usage:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> "User":  # type: ignore[name-defined]  # forward ref resolved at import time
    """
    FastAPI dependency — decode the Bearer JWT and return the matching User row.

    Steps:
        1. Extract the Bearer token from the Authorization header.
        2. Decode and verify the JWT signature / expiry.
        3. Assert token type is "access" (not "refresh").
        4. Look up the User by the UUID in `sub`.

    Raises:
        HTTP 401  on any invalid / expired token or missing user.

    Usage:
        @router.get("/protected")
        def endpoint(user: User = Depends(get_current_user)):
            ...
    """
    # Import here to avoid circular imports (User model imports Base which
    # imports nothing from security, but let's be safe).
    from app.models.user import User  # noqa: PLC0415

    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
    except JWTError:
        raise credentials_exc

    if payload.get("type") != "access":
        raise credentials_exc

    user_id: str | None = payload.get("sub")
    if not user_id:
        raise credentials_exc

    user: User | None = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exc

    return user


def get_current_active_user(
    current_user: Any = Depends(get_current_user),
) -> "User":  # type: ignore[name-defined]
    """
    FastAPI dependency — like get_current_user but also guards against
    soft-deleted accounts.

    Raises:
        HTTP 403  if the account's `deleted_at` field is set.

    Usage:
        @router.get("/profile")
        def endpoint(user: User = Depends(get_current_active_user)):
            ...
    """
    if current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated",
        )
    return current_user
