"""
API v1 router — aggregates all resource routers.
"""
from fastapi import APIRouter

from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.organizations import router as organizations_router
from app.routes.emissions import router as emissions_router
from app.routes.reports import router as reports_router

api_router = APIRouter()

api_router.include_router(auth_router,          prefix="/auth",          tags=["Auth"])
api_router.include_router(users_router,         prefix="/users",         tags=["Users"])
api_router.include_router(organizations_router, prefix="/organizations", tags=["Organizations"])
api_router.include_router(emissions_router,     prefix="/emissions",     tags=["Emissions"])
api_router.include_router(reports_router,       prefix="/reports",       tags=["Reports"])
