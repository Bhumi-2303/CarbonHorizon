"""
Schemas package — re-exports all public schemas for easy imports.

Usage:
    from app.schemas import APIResponse, RegisterRequest, ProfileResponse
    from app.schemas import TokenResponse, LoginRequest
"""
# Standard API envelope (use this in all routers)
from app.schemas.auth import (                    # noqa: F401
    APIResponse,
    ErrorDetail,
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    ProfileResponse,
    RegisterResponse,
    TokenAPIResponse,
    ProfileAPIResponse,
    RegisterAPIResponse,
)

# User schemas (legacy names kept for backward compat)
from app.schemas.user import (                    # noqa: F401
    UpdateProfileRequest,
    UserProfile,
    UserCreate,
    UserUpdate,
    UserResponse,
)

# Token schemas (legacy)
from app.schemas.token import TokenPayload         # noqa: F401
