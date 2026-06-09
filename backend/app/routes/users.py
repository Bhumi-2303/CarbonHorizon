"""
User routes — CRUD endpoints.
No logic yet; route stubs only.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/", summary="List users")
async def list_users():
    raise NotImplementedError


@router.post("/", summary="Create user", status_code=201)
async def create_user():
    raise NotImplementedError


@router.get("/me", summary="Get current user")
async def get_me():
    raise NotImplementedError


@router.get("/{user_id}", summary="Get user by ID")
async def get_user(user_id: int):
    raise NotImplementedError


@router.patch("/{user_id}", summary="Update user")
async def update_user(user_id: int):
    raise NotImplementedError


@router.delete("/{user_id}", summary="Delete user", status_code=204)
async def delete_user(user_id: int):
    raise NotImplementedError
