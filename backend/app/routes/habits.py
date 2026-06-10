"""
Habits router  —  /api/habits

Endpoints
---------
POST /api/habits/                  Log a habit completion for today
GET  /api/habits/                  List habit completions (filterable by date range)
GET  /api/habits/streak            Get the current habit streak for the user
GET  /api/habits/definitions       List all habit definitions (carbon saving factors)
GET  /api/habits/{habit_id}        Fetch a specific habit completion by ID
PATCH /api/habits/{habit_id}       Update a habit completion entry
DELETE /api/habits/{habit_id}      Delete a habit completion entry

All endpoints return {"detail": "not implemented"} until services are wired.
"""
from fastapi import APIRouter, status
from uuid import UUID

router = APIRouter()

_NOT_IMPLEMENTED = {"detail": "not implemented"}


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Log a sustainability habit completion",
)
async def log_habit():
    return _NOT_IMPLEMENTED


@router.get(
    "/",
    summary="List habit completions for the current user (supports date range filter)",
)
async def list_habits():
    return _NOT_IMPLEMENTED


@router.get(
    "/streak",
    summary="Get the current consecutive-day habit streak for the user",
)
async def get_habit_streak():
    return _NOT_IMPLEMENTED


@router.get(
    "/definitions",
    summary="List all habit definitions with their carbon saving factors",
)
async def list_habit_definitions():
    return _NOT_IMPLEMENTED


@router.get(
    "/{habit_id}",
    summary="Fetch a specific habit completion entry by ID",
)
async def get_habit(habit_id: UUID):
    return _NOT_IMPLEMENTED


@router.patch(
    "/{habit_id}",
    summary="Update a habit completion entry (notes, carbon_saved)",
)
async def update_habit(habit_id: UUID):
    return _NOT_IMPLEMENTED


@router.delete(
    "/{habit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a habit completion entry by ID",
)
async def delete_habit(habit_id: UUID):
    return _NOT_IMPLEMENTED
