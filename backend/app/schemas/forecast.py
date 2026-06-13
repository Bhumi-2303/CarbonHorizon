"""
Forecast Pydantic schemas for Carbon Horizon.

Provides:
  ForecastGenerateRequest  — POST /forecast/generate body
  ForecastPointResponse    — single time-series data point (month_offset, emission)
  ForecastResponse         — serialised Forecast ORM row (header + points)
  ForecastListResponse     — lightweight list item (no points embedded)

Typed APIResponse aliases:
  ForecastGenerateAPIResponse
  ForecastDetailAPIResponse
  ForecastListAPIResponse
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.enums import ForecastType
from app.schemas.auth import APIResponse


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CustomReductionRates(BaseModel):
    """
    User-defined monthly reduction rates (0.0 – 1.0) for custom_path forecasts.

    Each field is the *fractional* reduction per month for that category.
    For example, transport=0.05 means 5 % less transport emission every month.
    All fields are optional; omitted categories default to 0.0 (no change).
    """
    transport: float = Field(default=0.0, ge=0.0, le=1.0,
                             description="Monthly transport emission reduction rate (0–1)")
    energy:    float = Field(default=0.0, ge=0.0, le=1.0,
                             description="Monthly energy emission reduction rate (0–1)")
    food:      float = Field(default=0.0, ge=0.0, le=1.0,
                             description="Monthly food emission reduction rate (0–1)")
    waste:     float = Field(default=0.0, ge=0.0, le=1.0,
                             description="Monthly waste emission reduction rate (0–1)")


class ForecastGenerateRequest(BaseModel):
    """
    POST /api/v1/forecast/generate

    Parameters
    ----------
    forecast_type : ForecastType
        One of current_path / recommended_path / custom_path.
    custom_rates : CustomReductionRates | None
        Required only when forecast_type == custom_path.
        Ignored for the other two types.
    """
    forecast_type: ForecastType = Field(
        ...,
        description="Which forecast model to run.",
    )
    custom_rates: Optional[CustomReductionRates] = Field(
        None,
        description="Per-category monthly reduction rates. Only used for custom_path.",
    )


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ForecastPointResponse(BaseModel):
    """One data point in the forecast time-series."""
    id:                  uuid.UUID
    month_offset:        int
    predicted_emission:  float
    created_at:          datetime

    model_config = {"from_attributes": True}


class ForecastResponse(BaseModel):
    """
    Full Forecast session response — header + embedded time-series points.
    Returned by POST /generate and GET /{forecast_id}.
    """
    id:            uuid.UUID
    forecast_type: str
    created_at:    datetime
    updated_at:    datetime
    forecast_points: List[ForecastPointResponse]

    model_config = {"from_attributes": True}


class ForecastListItem(BaseModel):
    """
    Lightweight summary row returned by GET /history (no points embedded).
    """
    id:            uuid.UUID
    forecast_type: str
    point_count:   int                    # number of data points for the session
    created_at:    datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Typed APIResponse aliases
# ---------------------------------------------------------------------------

ForecastGenerateAPIResponse = APIResponse[ForecastResponse]
ForecastDetailAPIResponse   = APIResponse[ForecastResponse]
ForecastListAPIResponse     = APIResponse[List[ForecastListItem]]
