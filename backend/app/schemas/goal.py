from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict
import uuid

from app.models.enums import GoalStatus

class GoalBase(BaseModel):
    goal_name: str
    goal_description: Optional[str] = None
    target_reduction_percentage: Optional[float] = None
    target_emission_value: Optional[float] = None
    target_date: Optional[date] = None

class GoalCreate(GoalBase):
    pass

class GoalUpdate(BaseModel):
    goal_name: Optional[str] = None
    goal_description: Optional[str] = None
    target_reduction_percentage: Optional[float] = None
    target_emission_value: Optional[float] = None
    target_date: Optional[date] = None
    current_progress: Optional[float] = None
    status: Optional[GoalStatus] = None

class GoalResponse(GoalBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    current_progress: float
    status: GoalStatus
