"""
Dashboard router  —  /api/dashboard

Endpoints
---------
GET /api/dashboard/summary        Aggregated stats for the user's dashboard
GET /api/dashboard/history        Assessment history trend data
GET /api/dashboard/breakdown      Emission breakdown by category (latest)

All endpoints return {"detail": "not implemented"} until services are wired.
"""
from fastapi import APIRouter

router = APIRouter()

_NOT_IMPLEMENTED = {"detail": "not implemented"}


@router.get(
    "/summary",
    summary="Aggregated dashboard stats (latest assessment, active goals, streak, forecast snapshot)",
)
async def get_dashboard_summary():
    return _NOT_IMPLEMENTED


@router.get(
    "/history",
    summary="Assessment history trend — total_emission over time for charting",
)
async def get_assessment_history():
    return _NOT_IMPLEMENTED


@router.get(
    "/breakdown",
    summary="Emission category breakdown from the latest assessment (transport/energy/food/waste)",
)
async def get_emission_breakdown():
    return _NOT_IMPLEMENTED
