"""
Auth-specific Pydantic schemas for Carbon Horizon.

Provides:
  RegisterRequest   — POST /auth/register body
  LoginRequest      — POST /auth/login body
  TokenResponse     — token pair returned on login / refresh
  ProfileResponse   — authenticated user's public profile

Also provides the standard API response envelope used across all endpoints:

  APIResponse[T]  →  {"success": true,  "data": <T>}
                  →  {"success": false, "error": {"code": ..., "message": ...}}

Usage in routers
----------------
  from app.schemas.auth import APIResponse, ProfileResponse

  @router.get("/profile", response_model=APIResponse[ProfileResponse])
  async def get_profile(...):
      data = auth_service.get_profile(current_user)
      return APIResponse.ok(data)

  # On error (handled automatically by FastAPI exception handlers or manually):
      return APIResponse.fail("AUTH_001", "Invalid credentials")
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import AgeGroup, LifestyleType

# TypeVar for the generic data payload
T = TypeVar("T")


# ---------------------------------------------------------------------------
# Standard API response wrapper
# ---------------------------------------------------------------------------

class ErrorDetail(BaseModel):
    """Machine-readable error payload embedded in a failed APIResponse."""
    code: str           # e.g. "AUTH_001", "VALIDATION_ERROR"
    message: str        # human-readable description


class APIResponse(BaseModel, Generic[T]):
    """
    Standard JSON envelope for every Carbon Horizon API response.

    Success shape:
        {
          "success": true,
          "data": { ... }
        }

    Failure shape:
        {
          "success": false,
          "error": {
            "code": "AUTH_001",
            "message": "Invalid email or password"
          }
        }
    """
    success: bool
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None

    @classmethod
    def ok(cls, data: T) -> "APIResponse[T]":
        """Wrap a successful payload."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, code: str, message: str) -> "APIResponse[None]":
        """Wrap an error response (no data payload)."""
        return cls(success=False, error=ErrorDetail(code=code, message=message))

    model_config = {"arbitrary_types_allowed": True}


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    """
    POST /api/v1/auth/register

    All required fields for creating a Carbon Horizon account.
    Password must be at least 8 characters and not all digits.
    """
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["Priya Sharma"],
    )
    email: EmailStr = Field(..., examples=["priya@example.com"])
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Minimum 8 characters; must not be all digits.",
    )
    age_group: Optional[AgeGroup] = Field(
        None,
        description="One of: child, student, adult, senior",
    )
    lifestyle_type: Optional[LifestyleType] = Field(
        None,
        description="One of: student, professional, homemaker, retired",
    )
    city: Optional[str] = Field(None, max_length=100, examples=["Mumbai"])
    country: Optional[str] = Field(None, max_length=100, examples=["India"])

    @field_validator("password")
    @classmethod
    def password_not_all_digits(cls, v: str) -> str:
        if v.isdigit():
            raise ValueError("Password must not consist of digits only")
        return v


class LoginRequest(BaseModel):
    """POST /api/v1/auth/login"""
    email: EmailStr = Field(..., examples=["priya@example.com"])
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    """POST /api/v1/auth/refresh"""
    refresh_token: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class TokenResponse(BaseModel):
    """
    Token pair returned after a successful login or token refresh.

    access_token  — include in every authenticated request as:
                    Authorization: Bearer <access_token>
    refresh_token — use on POST /auth/refresh to get a new pair
    expires_in    — access token TTL in seconds (default 1 800 = 30 min)
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(
        default=1800,
        description="Access token TTL in seconds",
    )


class ProfileResponse(BaseModel):
    """
    Public profile of the authenticated user.
    Returned by GET /auth/profile and embedded in RegisterResponse.
    """
    id: uuid.UUID
    full_name: str
    email: EmailStr
    age_group: Optional[AgeGroup] = None
    lifestyle_type: Optional[LifestyleType] = None
    city: Optional[str] = None
    country: Optional[str] = None
    email_verified: bool
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RegisterResponse(BaseModel):
    """
    Returned on successful account creation.
    Contains the new user's profile and a welcome message.
    """
    user: ProfileResponse
    message: str = "Account created successfully. Please verify your email."


# ---------------------------------------------------------------------------
# Typed APIResponse aliases  (convenience — avoids repetitive Generic[T] syntax)
# ---------------------------------------------------------------------------

TokenAPIResponse    = APIResponse[TokenResponse]
ProfileAPIResponse  = APIResponse[ProfileResponse]
RegisterAPIResponse = APIResponse[RegisterResponse]
