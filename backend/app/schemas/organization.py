"""
Organization Pydantic schemas — no logic yet.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OrganizationBase(BaseModel):
    name: str
    industry: Optional[str] = None
    country: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
