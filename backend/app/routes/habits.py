from typing import List, Optional, Dict, Any
import uuid
from datetime import date

from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session

from app.core.security import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import APIResponse
from app.schemas.habit import HabitCreate, HabitUpdate, HabitResponse
from app.services.habit_service import HabitService

router = APIRouter()

@router.post("/log", response_model=APIResponse[HabitResponse], status_code=status.HTTP_201_CREATED, summary="Log a new habit or update an existing one for the date")
def log_habit(
    habit_in: HabitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    habit = HabitService.log_habit(db, current_user.id, habit_in)
    return APIResponse(success=True, data=habit)

@router.get("/", response_model=APIResponse[List[HabitResponse]], summary="Get all logged habits within an optional date range")
def get_habits(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    habits = HabitService.get_habits(db, current_user.id, start_date=start_date, end_date=end_date)
    return APIResponse(success=True, data=habits)

@router.get("/streak", response_model=APIResponse[Dict[str, int]], summary="Get current habit streak in days")
def get_streak(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    streak = HabitService.calculate_streak(db, current_user.id)
    return APIResponse(success=True, data={"streak": streak})

@router.get("/summary/weekly", response_model=APIResponse[Dict[str, Any]], summary="Get summary of habits logged in the last 7 days")
def get_weekly_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    summary = HabitService.get_weekly_summary(db, current_user.id)
    return APIResponse(success=True, data=summary)

@router.get("/summary/monthly", response_model=APIResponse[Dict[str, Any]], summary="Get summary of habits logged in the last 30 days")
def get_monthly_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    summary = HabitService.get_monthly_summary(db, current_user.id)
    return APIResponse(success=True, data=summary)

@router.patch("/{habit_id}", response_model=APIResponse[HabitResponse], summary="Update a logged habit")
def update_habit(
    habit_id: uuid.UUID,
    habit_in: HabitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    habit = HabitService.update_habit(db, current_user.id, habit_id, habit_in)
    return APIResponse(success=True, data=habit)

@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a logged habit")
def delete_habit(
    habit_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    HabitService.delete_habit(db, current_user.id, habit_id)
