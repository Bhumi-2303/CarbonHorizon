"""
FastAPI dependency injection providers.
These are injected into route handlers via Depends().
"""
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.security import JWTError
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.session import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


# ---------------------------------------------------------------------------
# Database session dependency
# ---------------------------------------------------------------------------

def get_db() -> Generator:
    """Yield a SQLAlchemy database session, then close it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Current user dependency (placeholder — wire to UserService when ready)
# ---------------------------------------------------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    """
    Validate JWT and return the current authenticated user.
    Raises HTTP 401 if the token is invalid or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # TODO: Replace with actual user lookup once UserService is implemented.
    # user = UserService.get_by_id(db, int(user_id))
    # if user is None:
    #     raise credentials_exception
    # return user
    return {"id": int(user_id)}  # Stub
