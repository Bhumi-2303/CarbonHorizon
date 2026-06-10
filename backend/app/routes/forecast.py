"""
Forecast router  —  /api/forecast

Endpoints
---------
POST /api/forecast/generate          Generate a new forecast for the user
GET  /api/forecast/                  List all forecast sessions for the user
GET  /api/forecast/{forecast_id}     Fetch a forecast session + all its points
DELETE /api/forecast/{forecast_id}   Delete a forecast session and its points

All endpoints return {"detail": "not implemented"} until services are wired.
"""
from fastapi import APIRouter, status
from uuid import UUID

router = APIRouter()

_NOT_IMPLEMENTED = {"detail": "not implemented"}


@router.post(
    "/generate",
    status_code=status.HTTP_201_CREATED,
    summary="Generate a new emission forecast and persist forecast points",
)
async def generate_forecast():
    return _NOT_IMPLEMENTED


@router.get(
    "/",
    summary="List all forecast sessions for the current user",
)
async def list_forecasts():
    return _NOT_IMPLEMENTED


@router.get(
    "/{forecast_id}",
    summary="Fetch a forecast session with all its time-series points",
)
async def get_forecast(forecast_id: UUID):
    return _NOT_IMPLEMENTED


@router.delete(
    "/{forecast_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a forecast session and all its associated points",
)
async def delete_forecast(forecast_id: UUID):
    return _NOT_IMPLEMENTED
