"""
Dashboard router  —  /api/v1/dashboard

Endpoints:
---------
GET /api/v1/dashboard/summary    Aggregated stats for the user's dashboard
GET /api/v1/dashboard            Backward-compatible summary alias (consumed by frontend client)
GET /api/v1/dashboard/history    Assessment history trend data
GET /api/v1/dashboard/breakdown  Emission breakdown by category from latest assessment
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.rate_limit import limiter
from app.core.security import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import APIResponse
from app.schemas.dashboard import (
    DashboardBreakdownResponse,
    DashboardHistoryResponse,
    DashboardSummaryResponse,
)
from app.services.dashboard_service import DashboardService

router = APIRouter()


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Aggregated dashboard stats (latest assessment, active goals, streak, forecast snapshot)",
)
@limiter.limit("60/minute")
async def get_dashboard_summary(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """
    Fetch aggregated stats for the user's dashboard:
    - Latest assessment metrics
    - Habit streak count
    - Active goals list and count
    - 3-month forecast snapshot
    - Trend percentage vs previous assessment
    """
    summary = DashboardService.get_summary(db, current_user.id)
    return APIResponse.ok(summary)


@router.get(
    "",
    response_model=DashboardSummaryResponse,
    summary="Dashboard summary alias for frontend compatibility",
)
@limiter.limit("60/minute")
async def get_dashboard_alias(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """
    Backward-compatible alias for GET /dashboard returning the full dashboard summary.
    """
    summary = DashboardService.get_summary(db, current_user.id)
    return APIResponse.ok(summary)


@router.get(
    "/",
    response_model=DashboardSummaryResponse,
    include_in_schema=False,
)
@limiter.limit("60/minute")
async def get_dashboard_slash_alias(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """
    Slash alias for GET /dashboard/ returning the full dashboard summary.
    """
    summary = DashboardService.get_summary(db, current_user.id)
    return APIResponse.ok(summary)


@router.get(
    "/history",
    response_model=DashboardHistoryResponse,
    summary="Assessment history trend — total_emission over time for charting",
)
@limiter.limit("60/minute")
async def get_assessment_history(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DashboardHistoryResponse:
    """
    Fetch all historical assessments for the authenticated user in descending
    chronological order, mapped with category emissions.
    """
    history = DashboardService.get_history(db, current_user.id)
    return APIResponse.ok(history)


@router.get(
    "/breakdown",
    response_model=DashboardBreakdownResponse,
    summary="Emission category breakdown from the latest assessment (transport/energy/food/waste)",
)
@limiter.limit("60/minute")
async def get_emission_breakdown(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> DashboardBreakdownResponse:
    """
    Fetch the emission category breakdown and percentages from the latest assessment.
    Returns 0-values gracefully if no assessment exists yet.
    """
    breakdown = DashboardService.get_breakdown(db, current_user.id)
    return APIResponse.ok(breakdown)
