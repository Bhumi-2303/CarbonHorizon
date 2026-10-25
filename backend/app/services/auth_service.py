"""
AuthService  —  authentication business logic for Carbon Horizon.

Responsibilities
----------------
register_user      Hash password with bcrypt, persist new User row,
                   return UserProfile + TokenResponse in one step.
login_user         Verify bcrypt hash, stamp last_login, return token pair.
refresh_tokens     Validate a refresh JWT, issue a fresh token pair
                   (with refresh token rotation — old refresh is revoked).
get_profile        Fetch the authenticated user's public profile.
update_profile     Patch mutable profile fields.
soft_delete_account  Set deleted_at; revoke all active sessions.
logout             Revoke the current access + optional refresh token.
logout_all         Revoke ALL active sessions for a user.

Token strategy
--------------
  Access  token: 30 min,  type="access"   — sent in every API request header
  Refresh token: 7 days,  type="refresh"  — used only on POST /auth/refresh

Both tokens include a unique `jti` (JWT ID) claim for server-side revocation.
On logout, the jti is added to a Redis blocklist with a TTL matching the
token's remaining lifetime. Redis auto-garbage-collects expired entries.

Refresh Token Rotation: each refresh request revokes the old refresh token
and issues an entirely new pair. Reuse of an already-revoked refresh token
is detected and logged as a potential token-theft signal.

Error handling
--------------
All public methods raise FastAPI HTTPException so callers (routers) stay thin.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from app.core.security import JWTError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    _calculate_ttl,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    is_token_revoked,
    revoke_all_user_tokens,
    revoke_token,
    track_user_session,
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

security_logger = logging.getLogger("security.token_revocation")
auth_logger = logging.getLogger("auth_debug")
auth_logger.setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

async def _token_response(user: User) -> TokenResponse:
    """
    Build a TokenResponse for *user*.

    Creates access + refresh tokens, tracks both JTIs in the user's
    Redis session set for logout-all support.
    """
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    # Track session JTIs in Redis for logout-all support
    access_claims = decode_token(access_token)
    refresh_claims = decode_token(refresh_token)

    # Track with the longest TTL (refresh token's)
    refresh_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    access_jti = access_claims.get("jti")
    refresh_jti = refresh_claims.get("jti")

    if access_jti:
        await track_user_session(str(user.id), access_jti, refresh_ttl)
    if refresh_jti:
        await track_user_session(str(user.id), refresh_jti, refresh_ttl)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def _assert_email_free(db: Session, email: str) -> None:
    """Raise HTTP 400 if email is already in use."""
    exists = (
        db.query(User).filter(func.lower(User.email) == email.lower()).first()
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
        .filter(
            func.lower(User.email) == email.lower(), User.deleted_at.is_(None)
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "We couldn't sign you in. "
                "Please check your email and password."
            ),
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

    Registers a new user, hashes password, saves to DB, returns
    ProfileResponse format.
    """
    _assert_email_free(db, payload.email)

    terms_dt = None
    if payload.terms_accepted:
        if payload.terms_accepted_at:
            try:
                clean_ts = payload.terms_accepted_at.replace("Z", "+00:00")
                terms_dt = datetime.fromisoformat(clean_ts)
            except Exception:
                terms_dt = datetime.now(timezone.utc)
        else:
            terms_dt = datetime.now(timezone.utc)

    user = User(
        id=uuid.uuid4(),
        full_name=payload.full_name,
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        age=payload.age,
        gender=payload.gender,
        age_group=payload.age_group,
        lifestyle_type=payload.lifestyle_type,
        city=payload.city,
        country=payload.country,
        state_province=payload.state_province,
        email_verified=False,
        terms_accepted=bool(payload.terms_accepted),
        terms_version=(
            payload.terms_version or ("2026-v1" if payload.terms_accepted else None)
        ),
        terms_accepted_at=terms_dt,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(user=ProfileResponse.model_validate(user))


# Precomputed bcrypt hash for constant-time dummy verification on non-existent accounts
# Prevents username enumeration through timing side-channel attacks.
DUMMY_BCRYPT_HASH = (
    "$2b$12$K.01q.6gXp7M7c2WkXbKMe0K5kF4bBvZzVlCq4b2Q8f4qM8vN4l0S"
)


async def login_user(db: Session, email: str, password: str) -> TokenResponse:
    """Verify credentials, stamp last_login, return token pair."""
    auth_logger.debug(f"LOGIN ATTEMPT: received email={email}")
    clean_email = email.strip().lower()

    user = (
        db.query(User)
        .filter(
            func.lower(User.email) == clean_email, User.deleted_at.is_(None)
        )
        .first()
    )

    if not user:
        auth_logger.debug(f"LOGIN ATTEMPT: user not found for email={email}")
        # Execute dummy bcrypt check to equalize response timing with existing accounts
        verify_password(password, DUMMY_BCRYPT_HASH)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "We couldn't sign you in. "
                "Please check your email and password."
            ),
        )

    auth_logger.debug(
        f"LOGIN ATTEMPT: stored hash length={len(user.password_hash)}"
    )

    is_valid = verify_password(password, user.password_hash)
    auth_logger.debug(f"LOGIN ATTEMPT: bcrypt verification result={is_valid}")

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "We couldn't sign you in. "
                "Please check your email and password."
            ),
        )

    # Stamp last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return await _token_response(user)


async def refresh_tokens(db: Session, payload: RefreshRequest) -> TokenResponse:
    """
    Validate a refresh token and issue a fresh token pair.

    Implements refresh token rotation:
    1. Decode and verify the old refresh token.
    2. Check if the old refresh token has been revoked (replay detection).
    3. Revoke the old refresh token's JTI (single-use enforcement).
    4. Issue a brand-new access + refresh pair.

    If the old refresh token's JTI is already revoked, this indicates
    potential token theft (replay attack) and is logged as a security warning.

    Raises:
        HTTP 401  on any invalid / expired / wrong-type / revoked token.
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

    # --- Refresh token rotation: check and revoke old token ---
    old_jti = claims.get("jti")
    if old_jti:
        # Check if already revoked (token replay / theft detection)
        if await is_token_revoked(old_jti):
            security_logger.warning(
                "SECURITY: Refresh token replay detected — possible token theft | "
                "jti=%s | user_id=%s | action=rejected",
                old_jti, user_id
            )
            raise credentials_exc

        # Revoke the old refresh token (single-use enforcement)
        ttl = _calculate_ttl(claims["exp"])
        await revoke_token(old_jti, ttl)
        security_logger.info(
            "Refresh token rotated | old_jti=%s | user_id=%s", old_jti, user_id
        )

    user = _get_active_user_by_id(db, user_id)
    return await _token_response(user)


async def logout(
    access_token_claims: dict,
    refresh_token: str | None,
    user_id: str,
) -> None:
    """
    Revoke the current access token and optionally the refresh token.

    Args:
        access_token_claims: Decoded claims dict from the access token.
        refresh_token: Optional refresh token string to also revoke.
        user_id: The authenticated user's UUID string.
    """
    # Revoke the access token
    access_jti = access_token_claims.get("jti")
    if access_jti:
        access_exp = access_token_claims.get("exp", 0)
        ttl = _calculate_ttl(access_exp)
        await revoke_token(access_jti, ttl)
        security_logger.info(
            "Logout: access token revoked | jti=%s | user_id=%s", access_jti, user_id
        )

    # Revoke the refresh token if provided
    if refresh_token:
        try:
            refresh_claims = decode_token(refresh_token)
            refresh_jti = refresh_claims.get("jti")
            if refresh_jti:
                refresh_exp = refresh_claims.get("exp", 0)
                ttl = _calculate_ttl(refresh_exp)
                await revoke_token(refresh_jti, ttl)
                security_logger.info(
                    "Logout: refresh token revoked | jti=%s | user_id=%s",
                    refresh_jti, user_id
                )
        except JWTError:
            # Refresh token is already expired or invalid — that's fine,
            # it's already unusable. Log and continue.
            security_logger.info(
                "Logout: refresh token already expired/invalid | user_id=%s", user_id
            )


async def logout_all(user_id: str) -> int:
    """
    Revoke ALL active sessions for a user.

    Args:
        user_id: The user's UUID string.

    Returns:
        Number of JTIs revoked.
    """
    count = await revoke_all_user_tokens(user_id)
    security_logger.info(
        "Logout-all completed | user_id=%s | revoked_count=%d", user_id, count
    )
    return count


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
    HTTP 404  if the user row disappears between request and commit
              (very rare).
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


async def soft_delete_account(db: Session, current_user: User) -> None:
    """
    Soft-delete the authenticated user's account.

    Sets deleted_at to the current UTC time and revokes all active sessions.
    The row is retained for 90 days per the data retention policy
    (see Backend Schema Documentation §21).

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

    # Revoke all active sessions — the user can no longer use any tokens
    try:
        await revoke_all_user_tokens(str(current_user.id))
        security_logger.info(
            "Account deactivated — all sessions revoked | user_id=%s",
            str(current_user.id)
        )
    except Exception as e:
        # Account is already soft-deleted; log but don't fail the request
        security_logger.warning(
            "Account deactivated but failed to revoke sessions | user_id=%s | error=%s",
            str(current_user.id), str(e)
        )
