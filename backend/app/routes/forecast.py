"""
Forecast router  —  /api/v1/forecast

Endpoints
---------
POST   /api/v1/forecast/generate        Run a forecast model + persist
GET    /api/v1/forecast/history         List all forecast sessions (newest first)
GET    /api/v1/forecast/{forecast_id}   Fetch a single forecast + all points
DELETE /api/v1/forecast/{forecast_id}   Delete a forecast session

All responses follow the standard APIResponse envelope:
    {"success": true,  "data": { ... }}
    {"success": false, "error": {"code": "...", "message": "..."}}
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import APIResponse
from app.schemas.forecast import (
    ForecastGenerateRequest,
    ForecastGenerateAPIResponse,
    ForecastDetailAPIResponse,
    ForecastListAPIResponse,
    ForecastListItem,
)
from app.services.forecast_service import ForecastService

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /generate  — compute and persist a forecast
# ---------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=ForecastGenerateAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new emission forecast and persist forecast points",
    description=(
        "Fetches the user's latest carbon assessment as the baseline, applies "
        "the requested forecast model (current / recommended / custom), and "
        "materialises predicted emissions at month offsets 3, 6, and 12. "
        "All rows are persisted to the database before returning."
    ),
)
async def generate_forecast(
    payload: ForecastGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ForecastGenerateAPIResponse:
    forecast = ForecastService.generate_forecast(db, current_user.id, payload)
    return APIResponse.ok(forecast)


# ---------------------------------------------------------------------------
# GET /history  — list all forecast sessions
# ---------------------------------------------------------------------------

@router.get(
    "/history",
    response_model=ForecastListAPIResponse,
    summary="List all forecast sessions for the current user",
    description="Returns a lightweight summary list (no embedded points).",
)
async def list_forecasts(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ForecastListAPIResponse:
    forecasts = ForecastService.get_forecast_history(db, current_user.id)
    # Convert ORM objects → ForecastListItem (schema)
    items = [
        ForecastListItem(
            id=f.id,
            forecast_type=f.forecast_type
            if isinstance(f.forecast_type, str)
            else f.forecast_type.value,
            point_count=len(f.forecast_points),
            created_at=f.created_at,
        )
        for f in forecasts
    ]
    return APIResponse.ok(items)


# ---------------------------------------------------------------------------
# GET /{forecast_id}  — fetch a specific forecast with all points
# ---------------------------------------------------------------------------

@router.get(
    "/{forecast_id}",
    response_model=ForecastDetailAPIResponse,
    summary="Fetch a forecast session with all its time-series points",
)
async def get_forecast(
    forecast_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ForecastDetailAPIResponse:
    forecast = ForecastService.get_forecast_by_id(db, current_user.id, forecast_id)
    return APIResponse.ok(forecast)


# ---------------------------------------------------------------------------
# DELETE /{forecast_id}  — remove a forecast session
# ---------------------------------------------------------------------------

@router.delete(
    "/{forecast_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a forecast session and all associated time-series points",
)
async def delete_forecast(
    forecast_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    ForecastService.delete_forecast(db, current_user.id, forecast_id)
    return None
