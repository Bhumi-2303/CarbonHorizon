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
  POST /refresh       Exchange refresh token (with rotation)

Authenticated (Bearer JWT):
  POST   /logout      Revoke current access + optional refresh token
  POST   /logout-all  Revoke ALL active sessions for the user
  GET    /profile     Current user's profile
  PUT    /profile     Update mutable profile fields
  DELETE /account     Soft-delete account (also revokes all sessions)

Stubs (not yet implemented):
  POST /verify-email
  POST /forgot-password
  POST /reset-password
"""

from fastapi import APIRouter, Depends, status, Request, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.security import (
    decode_token,
    get_current_active_user,
    get_db,
    _bearer_scheme,
)
from app.models.user import User
from app.schemas.auth import (
    APIResponse,
    LoginRequest,
    LogoutAPIResponse,
    LogoutAllAPIResponse,
    LogoutAllResponse,
    LogoutRequest,
    LogoutResponse,
    ProfileAPIResponse,
    RefreshRequest,
    RegisterAPIResponse,
    RegisterRequest,
    TokenAPIResponse,
)
from app.schemas.user import UpdateProfileRequest
import asyncio
from app.services import auth_service
from app.core.rate_limit import limiter
from app.core.client_ip import get_trusted_client_ip
from app.core.login_lockout import (
    check_login_lockout,
    check_account_hard_lockout,
    check_account_soft_threshold,
    record_login_failure,
    record_account_failure,
    clear_login_failures,
    clear_account_failures,
    make_lockout_key,
)
from app.core.turnstile import verify_turnstile_token

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
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: Session = Depends(get_db),
) -> RegisterAPIResponse:
    """
    Create a new Carbon Horizon account.

    - Verifies bot protection token and honeypot.
    - Hashes the password with bcrypt before storage.
    - Returns the new user's profile wrapped in
      `{"success": true, "data": ...}`.
    - Raises **409** if the email is already registered.
    """
    client_ip = get_trusted_client_ip(request)
    await verify_turnstile_token(payload.turnstile_token, remote_ip=client_ip)
    result = auth_service.register_user(db, payload)
    return APIResponse.ok(result)


@router.post(
    "/login",
    response_model=TokenAPIResponse,
    summary="Obtain access + refresh tokens",
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db),
) -> TokenAPIResponse:
    """
    Authenticate with email + password.

    - Derives client IP safely via trusted proxy resolution.
    - Enforces hard lockout for composite (account + IP) failures (5 in 15m).
    - Enforces soft threshold for account-wide failures across all IPs (20 in 1h),
      mandating Turnstile verification and applying progressive delay.
    - Verifies bot protection.
    - Verifies bcrypt hash.
    - Stamps `last_login` with current UTC time.
    - Returns `{"success": true, "data": {"access_token": ...,
      "expires_in": 1800}}`.
    - Raises **401** on invalid credentials, **403** when verification
      challenge required, and **429** on lockout.
    """
    client_ip = get_trusted_client_ip(request)
    lockout_key = make_lockout_key(payload.email, client_ip)

    # Check hard lockout for account+IP
    await check_login_lockout(lockout_key)

    # Check hard lockout ceiling across all IPs for the account
    await check_account_hard_lockout(payload.email)

    # Check soft threshold across all IPs for the account
    delay, require_turnstile = await check_account_soft_threshold(payload.email)
    if require_turnstile:
        if not payload.turnstile_token or not payload.turnstile_token.strip():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "Additional verification required due to repeated attempts "
                    "on this account. Please complete the verification challenge."
                ),
            )

    if delay > 0:
        await asyncio.sleep(delay)

    await verify_turnstile_token(payload.turnstile_token, remote_ip=client_ip)

    try:
        token = await auth_service.login_user(
            db, payload.email, payload.password
        )
        await clear_login_failures(lockout_key)
        await clear_account_failures(payload.email)
        return APIResponse.ok(token)
    except HTTPException as e:
        if e.status_code == status.HTTP_401_UNAUTHORIZED:
            await record_login_failure(lockout_key)
            await record_account_failure(payload.email)
        raise e


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

    Implements refresh token rotation: the old refresh token is revoked
    and a new pair is issued. Reuse of the old refresh token after rotation
    is detected as a potential token-theft signal.

    - Raises **401** if the token is expired, malformed, revoked, or
      not of type `refresh`.
    """
    token = await auth_service.refresh_tokens(db, payload)
    return APIResponse.ok(token)


# ---------------------------------------------------------------------------
# Authenticated endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/logout",
    response_model=LogoutAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout — revoke access token and optionally refresh token",
)
@limiter.limit("10/minute")
async def logout(
    request: Request,
    payload: LogoutRequest = LogoutRequest(),
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
    current_user: User = Depends(get_current_active_user),
) -> LogoutAPIResponse:
    """
    Revoke the current access token (from Authorization header) and
    optionally the refresh token (from request body).

    Both tokens' JTIs are added to the Redis blocklist with TTLs
    matching their remaining lifetimes.

    Returns **200** with confirmation message.
    """
    # Decode the raw access token to get its claims (jti, exp)
    access_claims = decode_token(credentials.credentials)

    await auth_service.logout(
        access_token_claims=access_claims,
        refresh_token=payload.refresh_token,
        user_id=str(current_user.id),
    )

    return APIResponse.ok(LogoutResponse())


@router.post(
    "/logout-all",
    response_model=LogoutAllAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Logout all devices — revoke ALL active sessions",
)
@limiter.limit("10/minute")
async def logout_all(
    request: Request,
    current_user: User = Depends(get_current_active_user),
) -> LogoutAllAPIResponse:
    """
    Revoke ALL active sessions for the authenticated user.

    Iterates the user's session set in Redis and blocklists every JTI.
    Use this when a user suspects their account is compromised.

    Returns **200** with the count of revoked sessions.
    """
    count = await auth_service.logout_all(user_id=str(current_user.id))
    return APIResponse.ok(LogoutAllResponse(revoked_count=count))


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
    Also revokes all active sessions.
    Returns **204 No Content**.
    Raises **409** if already deactivated.
    """
    await auth_service.soft_delete_account(db, current_user)
    return None


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


@router.post("/verify-email", summary="[Stub] Confirm email via token")
async def verify_email():
    return APIResponse.fail(
        "NOT_IMPLEMENTED", "Email verification not yet implemented"
    )


@router.post("/forgot-password", summary="[Stub] Send password-reset email")
async def forgot_password():
    return APIResponse.fail(
        "NOT_IMPLEMENTED", "Password reset not yet implemented"
    )


@router.post(
    "/reset-password", summary="[Stub] Apply new password via reset token"
)
async def reset_password():
    return APIResponse.fail(
        "NOT_IMPLEMENTED", "Password reset not yet implemented"
    )


@router.get(
    "/me",
    response_model=ProfileAPIResponse,
    summary="Alias for GET /profile",
    include_in_schema=False,
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> ProfileAPIResponse:
    return APIResponse.ok(auth_service.get_profile(current_user))
