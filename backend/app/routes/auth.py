"""
Auth router  —  /api/auth

Endpoints
---------
POST /api/auth/register     Create a new account
POST /api/auth/login        Obtain access + refresh tokens (OAuth2 password flow)
POST /api/auth/refresh      Exchange a refresh token for a new access token
POST /api/auth/logout       Invalidate the current refresh token
POST /api/auth/verify-email Confirm email address via token
POST /api/auth/forgot-password  Trigger password-reset email
POST /api/auth/reset-password   Apply a new password via reset token
GET  /api/auth/me           Return the authenticated user's profile

All endpoints return {"detail": "not implemented"} until services are wired.
"""
from fastapi import APIRouter, status

router = APIRouter()

_NOT_IMPLEMENTED = {"detail": "not implemented"}


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register():
    return _NOT_IMPLEMENTED


@router.post(
    "/login",
    summary="Obtain access + refresh tokens (OAuth2 password flow)",
)
async def login():
    return _NOT_IMPLEMENTED


@router.post(
    "/refresh",
    summary="Exchange a refresh token for a new access token",
)
async def refresh_token():
    return _NOT_IMPLEMENTED


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Invalidate the current refresh token",
)
async def logout():
    return _NOT_IMPLEMENTED


@router.post(
    "/verify-email",
    summary="Confirm email address via verification token",
)
async def verify_email():
    return _NOT_IMPLEMENTED


@router.post(
    "/forgot-password",
    summary="Send a password-reset email",
)
async def forgot_password():
    return _NOT_IMPLEMENTED


@router.post(
    "/reset-password",
    summary="Apply a new password via reset token",
)
async def reset_password():
    return _NOT_IMPLEMENTED


@router.get(
    "/me",
    summary="Return the authenticated user's profile",
)
async def get_me():
    return _NOT_IMPLEMENTED
