"""
JWT token Pydantic schemas.

TokenResponse  — returned to the client after login / refresh
TokenPayload   — decoded from a JWT (internal use only)
RefreshRequest — body for POST /auth/refresh
"""
from typing import Optional
from pydantic import BaseModel


class TokenResponse(BaseModel):
    """Access + refresh token pair returned to the caller."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # access token TTL in seconds


class TokenPayload(BaseModel):
    """Claims extracted from a decoded JWT."""
    sub: Optional[str] = None   # user UUID as string
    type: Optional[str] = None  # "access" | "refresh"


class RefreshRequest(BaseModel):
    """Request body for POST /auth/refresh."""
    refresh_token: str


# Keep backward-compatible alias used by existing stubs
Token = TokenResponse
