from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
import uuid

from app.models.enums import HabitType

class HabitBase(BaseModel):
    habit_type: HabitType
    activity_date: date
    notes: Optional[str] = None

class HabitCreate(HabitBase):
    pass

class HabitUpdate(BaseModel):
    habit_type: Optional[HabitType] = None
    activity_date: Optional[date] = None
    notes: Optional[str] = None
    completed: Optional[bool] = None

class HabitResponse(HabitBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    completed: bool
    carbon_saved: Optional[float] = None
    created_at: datetime
