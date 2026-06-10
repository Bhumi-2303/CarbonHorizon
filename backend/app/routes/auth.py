"""
Auth router  —  /api/v1/auth

Endpoints
---------
POST   /register      Create account (public)
POST   /login         Obtain token pair (public)
POST   /refresh       Exchange refresh token for new pair (public)
POST   /logout        Stateless logout — client discards tokens (authenticated)
GET    /profile       Return current user's profile (authenticated)
PUT    /profile       Update mutable profile fields (authenticated)
DELETE /account       Soft-delete account (authenticated)

Unimplemented stubs kept for future use:
POST   /verify-email
POST   /forgot-password
POST   /reset-password
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.models.user import User
from app.schemas.token import RefreshRequest, TokenResponse
from app.schemas.user import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    UpdateProfileRequest,
    UserProfile,
)
from app.services import auth_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterResponse:
    """
    Create a new Carbon Horizon account.

    - Hashes the password with bcrypt before storage.
    - Returns the new user's public profile.
    - Raises **409** if the email is already registered.
    """
    return auth_service.register_user(db, payload)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Obtain access + refresh tokens",
)
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Authenticate with email + password.

    - Verifies bcrypt hash.
    - Stamps `last_login` with current UTC time.
    - Returns `access_token` (30 min) and `refresh_token` (7 days).
    - Raises **401** on invalid credentials.
    """
    return auth_service.login_user(db, payload.email, payload.password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Exchange a refresh token for a new token pair",
)
async def refresh_token(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    """
    Use a valid refresh token to obtain a fresh access + refresh pair.

    - Raises **401** if the token is expired, malformed, or not of type `refresh`.
    """
    return auth_service.refresh_tokens(db, payload)


# ---------------------------------------------------------------------------
# Authenticated endpoints (Bearer token required)
# ---------------------------------------------------------------------------

@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Logout — instruct client to discard tokens",
)
async def logout(
    _current_user: User = Depends(get_current_active_user),
) -> None:
    """
    Stateless logout.

    Tokens are signed JWTs with a fixed expiry — there is no server-side
    token store to invalidate.  The client must delete the tokens from
    storage.  Access tokens expire in 30 min naturally.

    Returns **204 No Content**.
    """
    # TODO: when a Redis blocklist is added, record the jti here.
    return None


@router.get(
    "/profile",
    response_model=UserProfile,
    summary="Return the authenticated user's profile",
)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
) -> UserProfile:
    """
    Fetch the full public profile of the currently authenticated user.
    """
    return auth_service.get_profile(current_user)


@router.put(
    "/profile",
    response_model=UserProfile,
    summary="Update mutable profile fields",
)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    """
    Patch the authenticated user's profile.

    Only fields present in the request body are updated (partial update).
    Omitted fields are left unchanged.
    """
    return auth_service.update_profile(db, current_user, payload)


@router.delete(
    "/account",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete the authenticated user's account",
)
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Soft-delete the account by setting `deleted_at` to the current UTC time.

    - Data is retained for 90 days per the retention policy.
    - Existing tokens will be rejected by `get_current_active_user` on
      the next request.
    - Returns **204 No Content**.
    - Raises **409** if the account is already deactivated.
    """
    auth_service.soft_delete_account(db, current_user)
    return None


# ---------------------------------------------------------------------------
# Stub endpoints — not yet implemented
# ---------------------------------------------------------------------------

@router.post(
    "/verify-email",
    summary="[Stub] Confirm email address via verification token",
)
async def verify_email():
    return {"detail": "not implemented"}


@router.post(
    "/forgot-password",
    summary="[Stub] Send a password-reset email",
)
async def forgot_password():
    return {"detail": "not implemented"}


@router.post(
    "/reset-password",
    summary="[Stub] Apply a new password via reset token",
)
async def reset_password():
    return {"detail": "not implemented"}


@router.get(
    "/me",
    response_model=UserProfile,
    summary="Alias for GET /profile",
    include_in_schema=False,   # hidden from docs — use /profile instead
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserProfile:
    return auth_service.get_profile(current_user)
