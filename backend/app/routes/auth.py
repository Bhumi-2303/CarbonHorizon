"""
Auth router  —  /api/v1/auth

All responses are wrapped in the standard APIResponse envelope:
    {"success": true,  "data": { ... }}
    {"success": false, "error": {"code": "...", "message": "..."}}

Endpoints
---------
Public (no auth):
  POST /register      Create account
  POST /login         Obtain token pair
  POST /refresh       Exchange refresh token

Authenticated (Bearer JWT):
  POST   /logout      Stateless 204
  GET    /profile     Current user's profile
  PUT    /profile     Update mutable profile fields
  DELETE /account     Soft-delete account

Stubs (not yet implemented):
  POST /verify-email
  POST /forgot-password
  POST /reset-password
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import (
    APIResponse,
    LoginRequest,
    ProfileAPIResponse,
    ProfileResponse,
    RefreshRequest,
    RegisterAPIResponse,
    RegisterRequest,
    RegisterResponse,
    TokenAPIResponse,
    TokenResponse,
)
from app.schemas.user import UpdateProfileRequest
from app.services import auth_service

router = APIRouter()


# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/register",
    response_model=RegisterAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterAPIResponse:
    """
    Create a new Carbon Horizon account.

    - Hashes the password with bcrypt before storage.
    - Returns the new user's profile wrapped in `{"success": true, "data": ...}`.
    - Raises **409** if the email is already registered.
    """
    result = auth_service.register_user(db, payload)
    return APIResponse.ok(result)


@router.post(
    "/login",
    response_model=TokenAPIResponse,
    summary="Obtain access + refresh tokens",
)
async def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenAPIResponse:
    """
    Authenticate with email + password.

    - Verifies bcrypt hash.
    - Stamps `last_login` with current UTC time.
    - Returns `{"success": true, "data": {"access_token": ..., "expires_in": 1800}}`.
    - Raises **401** on invalid credentials.
    """
    token = auth_service.login_user(db, payload.email, payload.password)
    return APIResponse.ok(token)


@router.post(
    "/refresh",
    response_model=TokenAPIResponse,
    summary="Exchange a refresh token for a new token pair",
)
async def refresh_token(
    payload: RefreshRequest,
    db: Session = Depends(get_db),
) -> TokenAPIResponse:
    """
    Use a valid refresh token to get a fresh access + refresh pair.

    - Raises **401** if the token is expired, malformed, or not type `refresh`.
    """
    token = auth_service.refresh_tokens(db, payload)
    return APIResponse.ok(token)


# ---------------------------------------------------------------------------
# Authenticated endpoints
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
    Stateless logout — tokens are self-expiring JWTs with no server-side store.
    The client must discard the tokens from storage.
    Returns **204 No Content**.
    """
    # TODO: Redis blocklist for refresh tokens on logout
    return None


@router.get(
    "/profile",
    response_model=ProfileAPIResponse,
    summary="Return the authenticated user's profile",
)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
) -> ProfileAPIResponse:
    """
    Fetch the full profile of the currently authenticated user.

    Returns `{"success": true, "data": { <ProfileResponse> }}`.
    """
    profile = auth_service.get_profile(current_user)
    return APIResponse.ok(profile)


@router.put(
    "/profile",
    response_model=ProfileAPIResponse,
    summary="Update mutable profile fields",
)
async def update_profile(
    payload: UpdateProfileRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProfileAPIResponse:
    """
    Patch the authenticated user's profile (partial update).

    Only fields present in the request body are updated.
    Returns `{"success": true, "data": { <updated ProfileResponse> }}`.
    """
    profile = auth_service.update_profile(db, current_user, payload)
    return APIResponse.ok(profile)


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
    Soft-delete by setting `deleted_at`; data retained 90 days.
    Returns **204 No Content**.
    Raises **409** if already deactivated.
    """
    auth_service.soft_delete_account(db, current_user)
    return None


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

@router.post("/verify-email",   summary="[Stub] Confirm email via token")
async def verify_email():
    return APIResponse.fail("NOT_IMPLEMENTED", "Email verification not yet implemented")


@router.post("/forgot-password", summary="[Stub] Send password-reset email")
async def forgot_password():
    return APIResponse.fail("NOT_IMPLEMENTED", "Password reset not yet implemented")


@router.post("/reset-password",  summary="[Stub] Apply new password via reset token")
async def reset_password():
    return APIResponse.fail("NOT_IMPLEMENTED", "Password reset not yet implemented")


@router.get(
    "/me",
    response_model=ProfileAPIResponse,
    summary="Alias for GET /profile",
    include_in_schema=False,
)
async def get_me(current_user: User = Depends(get_current_active_user)) -> ProfileAPIResponse:
    return APIResponse.ok(auth_service.get_profile(current_user))
