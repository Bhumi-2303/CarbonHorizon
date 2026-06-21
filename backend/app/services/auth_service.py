"""
AuthService  —  authentication business logic for Carbon Horizon.

Responsibilities
----------------
register_user      Hash password with bcrypt, persist new User row,
                   return UserProfile + TokenResponse in one step.
login_user         Verify bcrypt hash, stamp last_login, return token pair.
refresh_tokens     Validate a refresh JWT, issue a fresh token pair.
get_profile        Fetch the authenticated user's public profile.
update_profile     Patch mutable profile fields.
soft_delete_account  Set deleted_at; the account is invisible to queries
                     but data is retained for 90 days per the retention policy.

Token strategy
--------------
  Access  token: 30 min,  type="access"   — sent in every API request header
  Refresh token: 7 days,  type="refresh"  — used only on POST /auth/refresh

Both tokens are signed with the app SECRET_KEY using HS256.  There is no
server-side token store: logout is stateless (client discards the tokens).
For production, add a Redis blocklist for refresh tokens on logout.

Error handling
--------------
All public methods raise FastAPI HTTPException so callers (routers) stay thin.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from app.core.security import JWTError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth import (
    ProfileResponse,
    RefreshRequest,
    RegisterRequest,
    RegisterResponse,
    TokenResponse,
)
from app.schemas.user import UpdateProfileRequest, validate_age_occupation


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _token_response(user: User) -> TokenResponse:
    """Build a TokenResponse for *user*."""
    return TokenResponse(
        access_token=create_access_token(subject=str(user.id)),
        refresh_token=create_refresh_token(subject=str(user.id)),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _assert_email_free(db: Session, email: str) -> None:
    """Raise HTTP 400 if email is already in use."""
    exists = (
        db.query(User)
        .filter(func.lower(User.email) == email.lower())
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already exists",
        )


def _get_active_user_by_email(db: Session, email: str) -> User:
    """Return an active User by email or raise HTTP 401."""
    user = (
        db.query(User)
        .filter(func.lower(User.email) == email.lower(), User.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="We couldn't sign you in. Please check your email and password.",
        )
    return user


def _get_active_user_by_id(db: Session, user_id: str | uuid.UUID) -> User:
    """Return an active User by UUID or raise HTTP 404."""
    if isinstance(user_id, str):
        try:
            parsed_id = uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
    else:
        parsed_id = user_id

    user = (
        db.query(User)
        .filter(User.id == parsed_id, User.deleted_at.is_(None))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def register_user(db: Session, payload: RegisterRequest) -> RegisterResponse:
    """
    Create a new user account.

    Registers a new user, hashes password, saves to DB, returns ProfileResponse format.
    """
    _assert_email_free(db, payload.email)

    user = User(
        id=uuid.uuid4(),
        full_name=payload.full_name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        age_group=payload.age_group,
        lifestyle_type=payload.lifestyle_type,
        city=payload.city,
        country=payload.country,
        email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(user=ProfileResponse.model_validate(user))


import logging
auth_logger = logging.getLogger("auth_debug")
auth_logger.setLevel(logging.DEBUG)

def login_user(db: Session, email: str, password: str) -> TokenResponse:
    auth_logger.debug(f"LOGIN ATTEMPT: received email={email}")
    try:
        user = _get_active_user_by_email(db, email)
        auth_logger.debug(f"LOGIN ATTEMPT: user found for email={email}")
    except HTTPException:
        auth_logger.debug(f"LOGIN ATTEMPT: user not found for email={email}")
        raise

    auth_logger.debug(f"LOGIN ATTEMPT: stored hash length={len(user.password_hash)}")
    
    is_valid = verify_password(password, user.password_hash)
    auth_logger.debug(f"LOGIN ATTEMPT: bcrypt verification result={is_valid}")

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="We couldn't sign you in. Please check your email and password.",
        )

    # Stamp last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return _token_response(user)


def refresh_tokens(db: Session, payload: RefreshRequest) -> TokenResponse:
    """
    Validate a refresh token and issue a fresh token pair.

    Steps
    -----
    1. Decode and verify the JWT signature.
    2. Assert token type is "refresh".
    3. Load the user from `sub`; ensure account is still active.
    4. Return a brand-new access + refresh pair.

    Raises
    ------
    HTTP 401  on any invalid / expired / wrong-type token.
    HTTP 404  if the user in `sub` no longer exists.
    """
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Session expired, please log in again",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        claims = decode_token(payload.refresh_token)
    except JWTError:
        raise credentials_exc

    if claims.get("type") != "refresh":
        raise credentials_exc

    user_id: str | None = claims.get("sub")
    if not user_id:
        raise credentials_exc

    user = _get_active_user_by_id(db, user_id)
    return _token_response(user)


def get_profile(current_user: User) -> ProfileResponse:
    """
    Return the authenticated user's public profile.

    No DB query needed — the User ORM object is already loaded by the
    get_current_active_user dependency.
    """
    return ProfileResponse.model_validate(current_user)


def update_profile(
    db: Session,
    current_user: User,
    payload: UpdateProfileRequest,
) -> ProfileResponse:
    """
    Patch mutable profile fields.

    Only fields explicitly set in the request body are updated (exclude_unset).
    Password changes are handled by a separate endpoint (not implemented here).

    Raises
    ------
    HTTP 404  if the user row disappears between request and commit (very rare).
    """
    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    try:
        validate_age_occupation(current_user.age, current_user.lifestyle_type)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )

    db.commit()
    db.refresh(current_user)
    return ProfileResponse.model_validate(current_user)


def soft_delete_account(db: Session, current_user: User) -> None:
    """
    Soft-delete the authenticated user's account.

    Sets deleted_at to the current UTC time.  The row is retained for 90 days
    per the data retention policy (see Backend Schema Documentation §21).

    After this call the client should discard its tokens — subsequent requests
    using the old access token will be rejected by get_current_active_user
    (which checks deleted_at).

    Raises
    ------
    HTTP 409  if the account is already soft-deleted (idempotency guard).
    """
    if current_user.is_deleted:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Account is already deactivated",
        )

    current_user.deleted_at = datetime.now(timezone.utc)
    db.commit()
