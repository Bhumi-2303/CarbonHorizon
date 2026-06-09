"""
Emission Pydantic schemas — no logic yet.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class EmissionBase(BaseModel):
    source: str
    scope: Literal[1, 2, 3]
    quantity_kg_co2e: float = Field(..., gt=0, description="CO₂ equivalent in kilograms")
    recorded_at: datetime
    notes: Optional[str] = None


class EmissionCreate(EmissionBase):
    organization_id: int


class EmissionUpdate(BaseModel):
    source: Optional[str] = None
    quantity_kg_co2e: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = None


class EmissionResponse(EmissionBase):
    id: int
    organization_id: int
    created_at: datetime

    model_config = {"from_attributes": True}
