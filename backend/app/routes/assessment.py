"""
Assessment router  —  /api/v1/assessment

All responses are wrapped in the standard APIResponse envelope:
    {"success": true,  "data": { ... }}
    {"success": false, "error": {"code": "...", "message": "..."}}
"""
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.security import get_current_active_user, get_db
from app.models.user import User
from app.schemas.auth import APIResponse
from app.schemas.assessment import (
    AssessmentInputs,
    AssessmentAPIResponse,
    AssessmentListAPIResponse,
)
from app.services.assessment_service import AssessmentService
from app.core.rate_limit import limiter

router = APIRouter()


@router.post(
    "/create",
    response_model=AssessmentAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new carbon assessment with emission inputs",
)
@limiter.limit("60/minute")
async def create_assessment(
    request: Request,
    payload: AssessmentInputs,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AssessmentAPIResponse:
    """
    Calculate user's carbon footprint and persist the assessment.
    Returns the mapped response.
    """
    result = AssessmentService.create_assessment(db, current_user.id, payload)
    return APIResponse.ok(result)


@router.get(
    "/history",
    response_model=AssessmentListAPIResponse,
    summary="List all carbon assessments for the current user",
)
@limiter.limit("60/minute")
async def get_history(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AssessmentListAPIResponse:
    """
    Retrieve user's historical carbon assessments in descending chronological order.
    """
    history = AssessmentService.get_assessment_history(db, current_user.id)
    return APIResponse.ok(history)


@router.get(
    "/latest",
    response_model=AssessmentAPIResponse,
    summary="Fetch the most recent carbon assessment",
)
@limiter.limit("60/minute")
async def get_latest_assessment(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AssessmentAPIResponse:
    """
    Fetch the currently authenticated user's latest assessment.
    Raises HTTP 404 if no assessments are found.
    """
    result = AssessmentService.get_latest_assessment(db, current_user.id)
    return APIResponse.ok(result)


@router.get(
    "/{assessment_id}",
    response_model=AssessmentAPIResponse,
    summary="Fetch a specific assessment by ID",
)
@limiter.limit("60/minute")
async def get_assessment(
    request: Request,
    assessment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AssessmentAPIResponse:
    """
    Fetch details of a specific assessment.
    Validates ownership; returns HTTP 404 if not found or unauthorized.
    """
    result = AssessmentService.get_assessment_by_id(db, current_user.id, assessment_id)
    return APIResponse.ok(result)


@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an assessment by ID",
)
@limiter.limit("60/minute")
async def delete_assessment(
    request: Request,
    assessment_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Delete a specific carbon assessment.
    Validates ownership; returns HTTP 404 if not found or unauthorized.
    """
    AssessmentService.delete_assessment(db, current_user.id, assessment_id)
    return None
