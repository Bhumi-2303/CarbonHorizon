"""
Assessment-specific Pydantic schemas for Carbon Horizon.

Provides:
  AssessmentInputs     — POST /assessment/create body
  AssessmentResponse   — assessment details returned on endpoints
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import TransportMode, DietType, AssessmentPeriod
from app.schemas.auth import APIResponse


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class AssessmentInputs(BaseModel):
    """
    POST /api/v1/assessment/create

    Inputs required to calculate a user's carbon footprint.
    """
    transport_mode: Optional[TransportMode] = Field(
        None,
        description="Mode of transportation, e.g., car, motorcycle, bus, train, flight, bicycle"
    )
    distance_km: Optional[float] = Field(
        None,
        ge=0,
        description="Distance traveled during the period in kilometers"
    )
    electricity_kwh: Optional[float] = Field(
        None,
        ge=0,
        description="Grid electricity consumed in kWh"
    )
    ac_hours: Optional[float] = Field(
        None,
        ge=0,
        description="Air conditioning usage in hours"
    )
    lpg_usage: Optional[float] = Field(
        None,
        ge=0,
        description="Liquefied petroleum gas usage in kg"
    )
    solar_usage: Optional[bool] = Field(
        None,
        description="Whether solar panels are used to offset electricity footprint"
    )
    diet_type: Optional[DietType] = Field(
        None,
        description="Primary diet type, e.g. vegetarian, mixed, non_vegetarian"
    )
    recycling_score: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="Recycling score representing frequency (scale 0-10)"
    )
    plastic_usage_score: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="Plastic usage score representing frequency (scale 0-10)"
    )
    household_size: Optional[int] = Field(
        None,
        ge=1,
        description="Number of people sharing the household"
    )
    assessment_period: Optional[AssessmentPeriod] = Field(
        AssessmentPeriod.monthly,
        description="Calculation frequency: daily, monthly, or annual"
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class AssessmentResponse(BaseModel):
    """
    Details of a processed carbon assessment.
    """
    assessment_id: uuid.UUID
    total_emission: float
    transport: float
    energy: float
    food: float
    waste: float
    carbon_score: int
    assessment_period: AssessmentPeriod
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Typed APIResponse aliases
# ---------------------------------------------------------------------------

AssessmentAPIResponse = APIResponse[AssessmentResponse]
AssessmentListAPIResponse = APIResponse[List[AssessmentResponse]]
