"""
Assessment router  —  /api/assessment

Endpoints
---------
POST /api/assessment/                    Submit a new carbon assessment
GET  /api/assessment/                    List the current user's assessments
GET  /api/assessment/latest              Fetch the most recent assessment
GET  /api/assessment/{assessment_id}     Fetch a specific assessment by ID
DELETE /api/assessment/{assessment_id}   Delete an assessment

All endpoints return {"detail": "not implemented"} until services are wired.
"""
from fastapi import APIRouter, status
from uuid import UUID

router = APIRouter()

_NOT_IMPLEMENTED = {"detail": "not implemented"}


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new carbon assessment with emission inputs",
)
async def create_assessment():
    return _NOT_IMPLEMENTED


@router.get(
    "/",
    summary="List all carbon assessments for the current user",
)
async def list_assessments():
    return _NOT_IMPLEMENTED


@router.get(
    "/latest",
    summary="Fetch the most recent carbon assessment",
)
async def get_latest_assessment():
    return _NOT_IMPLEMENTED


@router.get(
    "/{assessment_id}",
    summary="Fetch a specific assessment by ID",
)
async def get_assessment(assessment_id: UUID):
    return _NOT_IMPLEMENTED


@router.delete(
    "/{assessment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an assessment by ID",
)
async def delete_assessment(assessment_id: UUID):
    return _NOT_IMPLEMENTED
