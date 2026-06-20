import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, get_db
from app.services.progression_service import ProgressionService
from pydantic import BaseModel
from typing import Any

router = APIRouter()

class ProgressionResponse(BaseModel):
    success: bool
    data: dict[str, Any]

@router.get("", response_model=ProgressionResponse, summary="Get user progression")
def get_user_progression(
    db: Session = Depends(get_db),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Retrieve the current user's level, points, progress, and badges.
    """
    try:
        progression_data = ProgressionService.calculate_progression(db, current_user.id)
        return {"success": True, "data": progression_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
