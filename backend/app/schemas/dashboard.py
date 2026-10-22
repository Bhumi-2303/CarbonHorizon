"""
Dashboard Pydantic schemas.

Provides schemas for:
- DashboardSummaryData: aggregated stats (latest assessment,
  habit streak, goals, forecast, trend)
- DashboardBreakdownData: category breakdown and percentages
- DashboardHistoryItem: historical assessment list
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.schemas.auth import APIResponse


class DashboardAssessment(BaseModel):
    id: Optional[uuid.UUID] = None
    assessment_id: Optional[uuid.UUID] = None
    total_emission: float = 0.0
    transport_emission: float = 0.0
    energy_emission: float = 0.0
    food_emission: float = 0.0
    waste_emission: float = 0.0
    housing_emission: float = 0.0
    water_emission: float = 0.0
    digital_emission: float = 0.0
    shopping_emission: float = 0.0
    offsets_total: float = 0.0
    carbon_score: Optional[int] = None
    assessment_period: Optional[str] = None
    created_at: Optional[datetime] = None


class ForecastSummary(BaseModel):
    month_3_emission: float


class DashboardGoal(BaseModel):
    id: uuid.UUID
    goal_name: str
    goal_description: Optional[str] = None
    target_reduction_percentage: Optional[float] = None
    target_emission_value: Optional[float] = None
    current_progress: float = 0.0
    target_date: Optional[date] = None
    status: str


class DashboardSummaryData(BaseModel):
    latest_assessment: Optional[DashboardAssessment] = None
    trend_delta: float = 0.0
    trend_percentage: float = 0.0
    total_assessments: int = 0
    active_goals_count: int = 0
    active_goals: List[DashboardGoal] = Field(default_factory=list)
    current_habit_streak: int = 0
    forecast_summary: Optional[ForecastSummary] = None


class CategoryValues(BaseModel):
    transport: float = 0.0
    energy: float = 0.0
    food: float = 0.0
    waste: float = 0.0
    housing: float = 0.0
    water: float = 0.0
    digital: float = 0.0
    shopping: float = 0.0


class DashboardBreakdownData(BaseModel):
    total_emission: float = 0.0
    transport_emission: float = 0.0
    energy_emission: float = 0.0
    food_emission: float = 0.0
    waste_emission: float = 0.0
    categories: CategoryValues = Field(default_factory=CategoryValues)
    percentages: CategoryValues = Field(default_factory=CategoryValues)
    carbon_score: Optional[int] = None
    created_at: Optional[datetime] = None


class DashboardHistoryItem(DashboardAssessment):
    transport: Optional[float] = None
    energy: Optional[float] = None
    food: Optional[float] = None
    waste: Optional[float] = None


# Response model aliases wrapped in APIResponse
DashboardSummaryResponse = APIResponse[DashboardSummaryData]
DashboardBreakdownResponse = APIResponse[DashboardBreakdownData]
DashboardHistoryResponse = APIResponse[List[DashboardHistoryItem]]
