"""
Auth routes — login, logout, token refresh.
No logic yet; route stubs only.
"""
from fastapi import APIRouter

router = APIRouter()


@router.post("/login", summary="Obtain access + refresh tokens")
async def login():
    # TODO: Implement with AuthService.authenticate + AuthService.create_tokens
    raise NotImplementedError


@router.post("/refresh", summary="Refresh access token")
async def refresh_token():
    # TODO: Implement with AuthService.refresh_access_token
    raise NotImplementedError


@router.post("/logout", summary="Invalidate refresh token")
async def logout():
    # TODO: Implement token revocation
    raise NotImplementedError
