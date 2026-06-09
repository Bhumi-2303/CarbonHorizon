"""
Report routes — CRUD endpoints.
No logic yet; route stubs only.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="List reports")
async def list_reports():
    raise NotImplementedError


@router.post("/", summary="Create report", status_code=201)
async def create_report():
    raise NotImplementedError


@router.get("/{report_id}", summary="Get report by ID")
async def get_report(report_id: int):
    raise NotImplementedError


@router.patch("/{report_id}", summary="Update report")
async def update_report(report_id: int):
    raise NotImplementedError


@router.delete("/{report_id}", summary="Delete report", status_code=204)
async def delete_report(report_id: int):
    raise NotImplementedError
