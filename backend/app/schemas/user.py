"""
User Pydantic schemas — request bodies and API response shapes.

Aligns with the `users` ORM model columns (UUID PK, enums as str).
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator
import pydantic


# ---------------------------------------------------------------------------
# Enums (mirrored as str literals for Pydantic validation)
# ---------------------------------------------------------------------------

from app.models.enums import AgeGroup, LifestyleType, Gender


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

def validate_age_occupation(age: int | None, lifestyle: LifestyleType | None) -> None:
    if age is None or lifestyle is None:
        return
    
    if age < 18:
        valid = [LifestyleType.student]
    elif 18 <= age <= 59:
        valid = [
            LifestyleType.student,
            LifestyleType.professional,
            LifestyleType.homemaker,
            LifestyleType.house_helper,
            LifestyleType.self_employed,
            LifestyleType.business_owner,
        ]
    else:
        valid = [LifestyleType.retired, LifestyleType.consultant]
        
    if lifestyle not in valid:
        raise ValueError(f"Occupation '{lifestyle.value}' is not available for age {age}.")

class RegisterRequest(BaseModel):
    """POST /auth/register"""
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    age: int = Field(..., gt=0)
    gender: Gender
    age_group: Optional[AgeGroup] = None
    lifestyle_type: Optional[LifestyleType] = None
    country: str = Field(..., max_length=100)
    state_province: str = Field(..., max_length=100)
    city: str = Field(..., max_length=100)

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if v.isdigit():
            raise ValueError("Password must not be all digits")
        return v

    @pydantic.model_validator(mode="after")
    def validate_lifestyle(self) -> RegisterRequest:
        validate_age_occupation(self.age, self.lifestyle_type)
        return self


class LoginRequest(BaseModel):
    """POST /auth/login"""
    email: EmailStr
    password: str


class UpdateProfileRequest(BaseModel):
    """PUT /auth/profile — all fields optional"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, gt=0)
    gender: Optional[Gender] = None
    age_group: Optional[AgeGroup] = None
    lifestyle_type: Optional[LifestyleType] = None
    country: Optional[str] = Field(None, max_length=100)
    state_province: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class UserProfile(BaseModel):
    """Public user profile returned by GET /auth/profile and POST /auth/register."""
    id: uuid.UUID
    full_name: str
    email: EmailStr
    age: Optional[int] = None
    gender: Optional[Gender] = None
    age_group: Optional[AgeGroup] = None
    lifestyle_type: Optional[LifestyleType] = None
    country: Optional[str] = None
    state_province: Optional[str] = None
    city: Optional[str] = None
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
