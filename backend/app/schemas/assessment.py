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
        description=(
            "Mode of transportation, e.g., car, motorcycle, bus, train, "
            "flight, bicycle"
        ),
    )
    distance_km: Optional[float] = Field(
        None,
        ge=0,
        le=200000,
        description="Distance traveled during the period in kilometers",
    )
    electricity_kwh: Optional[float] = Field(
        None, ge=0, le=100000, description="Grid electricity consumed in kWh"
    )
    ac_hours: Optional[float] = Field(
        None, ge=0, le=8760, description="Air conditioning usage in hours"
    )
    lpg_usage: Optional[float] = Field(
        None, ge=0, le=5000, description="Liquefied petroleum gas usage in kg"
    )
    solar_usage: Optional[bool] = Field(
        None,
        description=(
            "Whether solar panels are used to offset electricity footprint"
        ),
    )
    diet_type: Optional[DietType] = Field(
        None,
        description=(
            "Primary diet type, e.g. vegetarian, mixed, non_vegetarian"
        ),
    )
    recycling_score: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="Recycling score representing frequency (scale 0-10)",
    )
    plastic_usage_score: Optional[int] = Field(
        None,
        ge=0,
        le=10,
        description="Plastic usage score representing frequency (scale 0-10)",
    )
    household_size: Optional[int] = Field(
        None, ge=1, le=50, description="Number of people sharing the household"
    )
    assessment_period: Optional[AssessmentPeriod] = Field(
        AssessmentPeriod.monthly,
        description="Calculation frequency: daily, monthly, or annual",
    )

    # ------------------ EXTENDED FIELDS ------------------

    # 1. Transport Extended
    vehicle_type: Optional[str] = Field(None, max_length=50)
    fuel_type: Optional[str] = Field(None, max_length=50)
    trips_per_week: Optional[int] = Field(None, ge=0, le=200)
    public_transport_usage: Optional[str] = Field(None, max_length=50)
    carpooling_frequency: Optional[str] = Field(None, max_length=50)
    air_travel_frequency: Optional[str] = Field(None, max_length=50)
    train_travel_frequency: Optional[str] = Field(None, max_length=50)
    walking_cycling_hours: Optional[float] = Field(None, ge=0, le=168)

    # 2. Energy Extended
    energy_efficiency_rating: Optional[str] = Field(None, max_length=50)
    heating_type: Optional[str] = Field(None, max_length=50)

    # 3. Food Extended
    local_food_frequency: Optional[str] = Field(None, max_length=50)
    food_waste_percentage: Optional[float] = Field(None, ge=0, le=100)

    # 4. Water
    daily_water_liters: Optional[float] = Field(None, ge=0, le=20000)
    shower_duration_minutes: Optional[float] = Field(None, ge=0, le=300)
    water_heating_type: Optional[str] = Field(None, max_length=50)

    # 5. Waste Extended
    composting_frequency: Optional[str] = Field(None, max_length=50)
    ewaste_disposal_method: Optional[str] = Field(None, max_length=50)

    # 6. Housing
    house_size_sqm: Optional[float] = Field(None, ge=0, le=10000)
    home_insulation_level: Optional[str] = Field(None, max_length=50)

    # 7. Digital
    screen_time_hours: Optional[float] = Field(None, ge=0, le=24)
    streaming_hours: Optional[float] = Field(None, ge=0, le=24)
    gaming_hours: Optional[float] = Field(None, ge=0, le=24)

    # 8. Shopping
    new_clothes_monthly: Optional[int] = Field(None, ge=0, le=100)
    second_hand_purchases: Optional[str] = Field(None, max_length=50)
    electronics_purchases_yearly: Optional[int] = Field(None, ge=0, le=100)

    # 9. Occupation
    commute_days_per_week: Optional[int] = Field(None, ge=0, le=7)
    remote_work_percentage: Optional[float] = Field(None, ge=0, le=100)

    # 10. Geographic
    assessment_country: Optional[str] = Field(None, max_length=100)
    assessment_state: Optional[str] = Field(None)
    assessment_city: Optional[str] = Field(None)

    # 12. Offsets
    composting_active: Optional[bool] = Field(None)
    tree_planting_count: Optional[int] = Field(None, ge=0)
    reusable_products_usage: Optional[str] = Field(None)
    green_transport_choices: Optional[bool] = Field(None)


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
    housing: Optional[float] = 0.0
    water: Optional[float] = 0.0
    digital: Optional[float] = 0.0
    shopping: Optional[float] = 0.0
    offsets: Optional[float] = 0.0
    carbon_score: int
    assessment_period: AssessmentPeriod
    created_at: datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Typed APIResponse aliases
# ---------------------------------------------------------------------------

AssessmentAPIResponse = APIResponse[AssessmentResponse]
AssessmentListAPIResponse = APIResponse[List[AssessmentResponse]]
