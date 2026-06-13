from typing import List
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import APIResponse
from app.schemas.goal import GoalCreate, GoalUpdate, GoalResponse
from app.services.goal_service import GoalService

router = APIRouter()

@router.post("/", response_model=APIResponse[GoalResponse], status_code=status.HTTP_201_CREATED, summary="Create a new sustainability goal")
def create_goal(
    goal_in: GoalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = GoalService.create_goal(db, current_user.id, goal_in)
    return APIResponse(success=True, data=goal)

@router.get("/", response_model=APIResponse[List[GoalResponse]], summary="List all goals for the current user (all statuses)")
def list_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goals = GoalService.get_goals(db, current_user.id)
    return APIResponse(success=True, data=goals)

@router.get("/active", response_model=APIResponse[List[GoalResponse]], summary="List only active goals for the current user")
def list_active_goals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goals = GoalService.get_active_goals(db, current_user.id)
    return APIResponse(success=True, data=goals)

@router.get("/{goal_id}", response_model=APIResponse[GoalResponse], summary="Fetch a specific goal by ID")
def get_goal(
    goal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = GoalService.get_goal(db, current_user.id, goal_id)
    return APIResponse(success=True, data=goal)

@router.patch("/{goal_id}", response_model=APIResponse[GoalResponse], summary="Update a goal's name, target values, progress, or status")
def update_goal(
    goal_id: uuid.UUID,
    goal_in: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    goal = GoalService.update_goal(db, current_user.id, goal_id, goal_in)
    return APIResponse(success=True, data=goal)

@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a goal by ID")
def delete_goal(
    goal_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    GoalService.delete_goal(db, current_user.id, goal_id)
