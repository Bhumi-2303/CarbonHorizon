"""
Goals router  —  /api/goals

Endpoints
---------
POST /api/goals/                 Create a new sustainability goal
GET  /api/goals/                 List all goals for the current user
GET  /api/goals/active           List only active goals
GET  /api/goals/{goal_id}        Fetch a goal by ID
PATCH /api/goals/{goal_id}       Update a goal (name, target, progress, status)
DELETE /api/goals/{goal_id}      Delete a goal

All endpoints return {"detail": "not implemented"} until services are wired.
"""
from fastapi import APIRouter, status
from uuid import UUID

router = APIRouter()

_NOT_IMPLEMENTED = {"detail": "not implemented"}


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Create a new sustainability goal",
)
async def create_goal():
    return _NOT_IMPLEMENTED


@router.get(
    "/",
    summary="List all goals for the current user (all statuses)",
)
async def list_goals():
    return _NOT_IMPLEMENTED


@router.get(
    "/active",
    summary="List only active goals for the current user",
)
async def list_active_goals():
    return _NOT_IMPLEMENTED


@router.get(
    "/{goal_id}",
    summary="Fetch a specific goal by ID",
)
async def get_goal(goal_id: UUID):
    return _NOT_IMPLEMENTED


@router.patch(
    "/{goal_id}",
    summary="Update a goal's name, target values, progress, or status",
)
async def update_goal(goal_id: UUID):
    return _NOT_IMPLEMENTED


@router.delete(
    "/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a goal by ID",
)
async def delete_goal(goal_id: UUID):
    return _NOT_IMPLEMENTED
