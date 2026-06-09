"""
Organization routes — CRUD endpoints.
No logic yet; route stubs only.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="List organizations")
async def list_organizations():
    raise NotImplementedError


@router.post("/", summary="Create organization", status_code=201)
async def create_organization():
    raise NotImplementedError


@router.get("/{org_id}", summary="Get organization by ID")
async def get_organization(org_id: int):
    raise NotImplementedError


@router.patch("/{org_id}", summary="Update organization")
async def update_organization(org_id: int):
    raise NotImplementedError


@router.delete("/{org_id}", summary="Delete organization", status_code=204)
async def delete_organization(org_id: int):
    raise NotImplementedError
