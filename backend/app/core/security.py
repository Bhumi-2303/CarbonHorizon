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
2. JWT helpers        — PyJWT (create / decode) with JTI claims
3. Token revocation   — Redis-backed JTI blocklist
4. FastAPI auth deps  — get_current_user, get_current_active_user, get_db

bcrypt note
-----------
passlib 1.7.4 is incompatible with bcrypt ≥ 4.0 on Python 3.14
(missing __about__ attribute; 72-byte probe crash).
We call bcrypt.hashpw / bcrypt.checkpw directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

import bcrypt
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt.exceptions import InvalidTokenError as JWTError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal

security_logger = logging.getLogger("security.token_revocation")

# ---------------------------------------------------------------------------
# 1. Password hashing
# ---------------------------------------------------------------------------


def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain* text password. Rejects > 72 UTF-8 bytes."""
    encoded = plain.encode("utf-8")
    if len(encoded) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password cannot exceed 72 bytes in UTF-8 encoding",
        )
    try:
        return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("utf-8")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password cannot exceed 72 bytes in UTF-8 encoding",
        )


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if *plain* matches the bcrypt *hashed* password. Never raises 500."""
    try:
        encoded = plain.encode("utf-8")
        if len(encoded) > 72:
            return False
        return bcrypt.checkpw(encoded, hashed.encode("utf-8"))
    except Exception:
        return False


# ---------------------------------------------------------------------------
# 2. JWT helpers (with JTI claims)
# ---------------------------------------------------------------------------


def create_access_token(
    subject: Any,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token with a unique JTI claim.

    Args:
        subject:       The unique identifier to embed in `sub`
                       (usually user UUID).
        expires_delta: Override the default TTL
                       (settings.ACCESS_TOKEN_EXPIRE_MINUTES).

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + (
        expires_delta
        or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


def create_refresh_token(subject: Any) -> str:
    """
    Create a signed JWT refresh token with a unique JTI claim.
    (TTL = settings.REFRESH_TOKEN_EXPIRE_DAYS).

    Args:
        subject: The unique identifier to embed in `sub` (usually user UUID).

    Returns:
        Signed JWT string.
    """
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4()),
        "type": "refresh",
    }
    return jwt.encode(
        payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT.

    Args:
        token: Signed JWT string.

    Returns:
        Decoded claims dict.

    Raises:
        JWTError: If the token is expired, malformed, or has an
                  invalid signature.
    """
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
    except (
        jwt.ExpiredSignatureError,
        jwt.InvalidSignatureError,
        jwt.DecodeError,
        jwt.InvalidTokenError,
    ) as e:
        raise JWTError(str(e)) from e


def _calculate_ttl(exp_timestamp: int | float) -> int:
    """
    Calculate remaining TTL in seconds from an exp claim timestamp.

    Returns at least 1 second to prevent negative/zero TTL in Redis SET EX.
    Handles clock skew and already-expired tokens gracefully.
    """
    remaining = int(exp_timestamp - datetime.now(timezone.utc).timestamp())
    return max(remaining, 1)


# ---------------------------------------------------------------------------
# 3. Token revocation — Redis-backed JTI blocklist
# ---------------------------------------------------------------------------

async def revoke_token(jti: str, ttl_seconds: int) -> None:
    """
    Add a JTI to the Redis blocklist with the given TTL.

    The key auto-expires when the original token would have expired,
    so Redis doesn't grow unbounded.

    Args:
        jti: The JWT ID to revoke.
        ttl_seconds: Time-to-live in seconds (clamped to >= 1).
    """
    from app.core.redis_client import get_redis

    r = get_redis()
    if r is None:
        security_logger.warning(
            "Redis not available — cannot revoke token | jti=%s", jti
        )
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )
        return

    ttl = max(ttl_seconds, 1)
    await r.set(f"revoked_token:{jti}", "1", ex=ttl)
    security_logger.info(
        "Token revoked | jti=%s | ttl=%ds", jti, ttl
    )


async def atomic_rotate_refresh_token(jti: str, ttl_seconds: int) -> bool:
    """
    Atomically registers a refresh token's JTI as revoked using Redis SET NX.
    Returns True if the token was successfully rotated/revoked (first time seen).
    Returns False if the token was ALREADY revoked (replay attack / reuse).
    In production, fails closed (503) if Redis is unavailable.
    """
    from app.core.redis_client import get_redis

    r = get_redis()
    if r is None:
        if settings.is_production:
            security_logger.error(
                "Redis unavailable during refresh token rotation in production"
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )
        security_logger.warning(
            "Redis not available in development/test — skipping revocation | jti=%s",
            jti,
        )
        return True

    ttl = max(ttl_seconds, 1)
    try:
        # SET key value EX ttl NX returns True if key was set,
        # None/False if key already existed.
        res = await r.set(f"revoked_token:{jti}", "1", ex=ttl, nx=True)
        return bool(res)
    except Exception as e:
        security_logger.error(
            "Redis error during atomic token rotation: %s", str(e)
        )
        if settings.is_production:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable",
            )
        return True


async def is_token_revoked(jti: str) -> bool:
    """
    Check if a JTI has been revoked.

    Args:
        jti: The JWT ID to check.

    Returns:
        True if the token is in the blocklist.

    Raises:
        HTTPException(503) if Redis is unreachable and REDIS_FAIL_OPEN is False.
    """
    from app.core.redis_client import get_redis

    r = get_redis()
    if r is None:
        # No Redis configured — tokens are not revocable
        return False

    try:
        return bool(await r.exists(f"revoked_token:{jti}"))
    except Exception as e:
        if settings.REDIS_FAIL_OPEN:
            security_logger.warning(
                "Redis unavailable, fail-open policy — allowing token | "
                "jti=%s | error=%s",
                jti, str(e)
            )
            return False
        else:
            security_logger.error(
                "Redis unavailable, fail-closed policy — rejecting request | "
                "jti=%s | error=%s",
                jti, str(e)
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service temporarily unavailable. "
                       "Please try again.",
            )


async def track_user_session(user_id: str, jti: str, ttl_seconds: int) -> None:
    """
    Track an active session JTI in the user's session set.

    Used by logout-all to enumerate and revoke all sessions for a user.

    Args:
        user_id: The user's UUID string.
        jti: The JWT ID to track.
        ttl_seconds: TTL for the session set (matches the longest-lived token).
    """
    from app.core.redis_client import get_redis

    r = get_redis()
    if r is None:
        return

    key = f"user_sessions:{user_id}"
    ttl = max(ttl_seconds, 1)
    try:
        await r.sadd(key, jti)
        # Refresh the set's expiry to at least the new token's TTL
        current_ttl = await r.ttl(key)
        if current_ttl < ttl:
            await r.expire(key, ttl)
    except Exception as e:
        security_logger.warning(
            "Failed to track user session | user_id=%s | jti=%s | error=%s",
            user_id, jti, str(e)
        )


async def revoke_all_user_tokens(user_id: str) -> int:
    """
    Revoke ALL active sessions for a user (logout-all).

    Iterates the user_sessions:{user_id} set, blocklists each JTI,
    then deletes the set.

    Args:
        user_id: The user's UUID string.

    Returns:
        Number of JTIs revoked.

    Raises:
        HTTPException(503) if Redis is unreachable.
    """
    from app.core.redis_client import get_redis

    r = get_redis()
    if r is None:
        security_logger.warning(
            "Redis not available — cannot revoke all tokens | user_id=%s", user_id
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token revocation service unavailable. Please try again.",
        )

    try:
        key = f"user_sessions:{user_id}"
        jtis = await r.smembers(key)

        if not jtis:
            security_logger.info(
                "Logout-all: no active sessions found | user_id=%s", user_id
            )
            return 0

        # Blocklist each JTI with a conservative TTL
        # (max refresh token lifetime as upper bound since we don't know
        # which are access vs refresh tokens)
        max_ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600

        pipe = r.pipeline()
        for jti in jtis:
            pipe.set(f"revoked_token:{jti}", "1", ex=max_ttl)
        pipe.delete(key)
        await pipe.execute()

        count = len(jtis)
        security_logger.info(
            "Logout-all completed | user_id=%s | revoked_count=%d", user_id, count
        )
        return count
    except HTTPException:
        raise
    except Exception as e:
        security_logger.error(
            "Failed to revoke all tokens | user_id=%s | error=%s", user_id, str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Token revocation service unavailable. Please try again.",
        )


# ---------------------------------------------------------------------------
# 4. FastAPI dependencies
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


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> (
    "User"
):  # type: ignore[name-defined]
    """
    FastAPI dependency — decode the Bearer JWT, check blocklist, return User.

    Steps:
        1. Extract the Bearer token from the Authorization header.
        2. Decode and verify the JWT signature / expiry.
        3. Assert token type is "access" (not "refresh").
        4. If jti is present, check the Redis blocklist.
        5. Look up the User by the UUID in `sub`.

    Raises:
        HTTP 401  on any invalid / expired / revoked token or missing user.
        HTTP 503  if Redis is unreachable and REDIS_FAIL_OPEN is False.

    Usage:
        @router.get("/protected")
        async def endpoint(user: User = Depends(get_current_user)):
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

    revoked_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token has been revoked, please log in again",
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

    # --- JTI blocklist check ---
    jti = payload.get("jti")
    if jti:
        if await is_token_revoked(jti):
            security_logger.warning(
                "Revoked token used | jti=%s | user_id=%s", jti, user_id
            )
            raise revoked_exc
    else:
        # Legacy token without jti — allow through with warning
        security_logger.warning(
            "Token without jti claim detected — not revocable | user_id=%s", user_id
        )

    try:
        uuid_obj = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exc

    user: User | None = db.query(User).filter(User.id == uuid_obj).first()
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


def set_secure_cookie(
    response: Any,
    key: str,
    value: str,
    max_age: Optional[int] = None,
    path: str = "/",
    domain: Optional[str] = None,
    secure: bool = True,
    httponly: bool = True,
    samesite: str = "lax",
) -> None:
    """
    Set an HTTP cookie with strict security defaults:
    Secure=True, HttpOnly=True, SameSite=lax (or strict).
    """
    response.set_cookie(
        key=key,
        value=value,
        max_age=max_age,
        path=path,
        domain=domain,
        secure=secure,
        httponly=httponly,
        samesite=samesite,
    )
