"""
User Pydantic schemas — request bodies and API response shapes.

Aligns with the `users` ORM model columns (UUID PK, enums as str).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Enums (mirrored as str literals for Pydantic validation)
# ---------------------------------------------------------------------------

from app.models.enums import AgeGroup, LifestyleType


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    """POST /auth/register"""
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    age_group: Optional[AgeGroup] = None
    lifestyle_type: Optional[LifestyleType] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if v.isdigit():
            raise ValueError("Password must not be all digits")
        return v


class LoginRequest(BaseModel):
    """POST /auth/login"""
    email: EmailStr
    password: str


class UpdateProfileRequest(BaseModel):
    """PUT /auth/profile — all fields optional"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    age_group: Optional[AgeGroup] = None
    lifestyle_type: Optional[LifestyleType] = None


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    """Public user profile returned by GET /auth/profile and POST /auth/register."""
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
    """Response body for successful registration."""
    user: UserProfile
    message: str = "Account created successfully. Please verify your email."


# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------
UserCreate = RegisterRequest
UserUpdate = UpdateProfileRequest
UserResponse = UserProfile
