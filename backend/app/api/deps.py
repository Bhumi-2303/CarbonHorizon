"""
FastAPI dependency helpers.

get_db           — yields a SQLAlchemy Session; rolls back on error, always closes
get_current_user — decodes Bearer JWT and returns the authenticated User row
get_current_active_user — same but asserts the account is not soft-deleted
"""
from __future__ import annotations

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.user import User

# OAuth2 bearer scheme — reads Authorization: Bearer <token>
_bearer = HTTPBearer(auto_error=True)


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """Yield a database session for the duration of a request."""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """
    Decode the Bearer JWT and return the matching User row.

    Raises HTTP 401 if:
      • Token is missing / malformed
      • Token type is not "access"
      • User UUID in `sub` does not exist in the DB
    """
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
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Like get_current_user but also asserts the account has not been soft-deleted.
    Raises HTTP 403 if deleted_at is set.
    """
    if current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account has been deactivated",
        )
    return current_user
