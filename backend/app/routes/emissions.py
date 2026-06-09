"""
Emission routes — CRUD endpoints.
No logic yet; route stubs only.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="List emissions")
async def list_emissions():
    raise NotImplementedError


@router.post("/", summary="Record emission", status_code=201)
async def create_emission():
    raise NotImplementedError


@router.get("/{emission_id}", summary="Get emission by ID")
async def get_emission(emission_id: int):
    raise NotImplementedError


@router.patch("/{emission_id}", summary="Update emission")
async def update_emission(emission_id: int):
    raise NotImplementedError


@router.delete("/{emission_id}", summary="Delete emission", status_code=204)
async def delete_emission(emission_id: int):
    raise NotImplementedError
