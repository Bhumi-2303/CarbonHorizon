"""
API v1 router — aggregates all resource routers.

Route map
---------
/api/v1/auth           →  auth.py
/api/v1/assessment     →  assessment.py
/api/v1/dashboard      →  dashboard.py
/api/v1/simulator      →  simulator.py
/api/v1/forecast       →  forecast.py
/api/v1/goals          →  goals.py
/api/v1/habits         →  habits.py
/api/v1/coach          →  coach.py
"""
from fastapi import APIRouter

from app.routes.auth import router as auth_router
from app.routes.assessment import router as assessment_router
from app.routes.dashboard import router as dashboard_router
from app.routes.simulator import router as simulator_router
from app.routes.forecast import router as forecast_router
from app.routes.goals import router as goals_router
from app.routes.habits import router as habits_router
from app.routes.coach import router as coach_router
from app.routes.progression import router as progression_router

api_router = APIRouter()

api_router.include_router(auth_router,       prefix="/auth",       tags=["Auth"])
api_router.include_router(assessment_router, prefix="/assessment",  tags=["Assessment"])
api_router.include_router(dashboard_router,  prefix="/dashboard",   tags=["Dashboard"])
api_router.include_router(simulator_router,  prefix="/simulator",   tags=["Simulator"])
api_router.include_router(forecast_router,   prefix="/forecast",    tags=["Forecast"])
api_router.include_router(goals_router,      prefix="/goals",       tags=["Goals"])
api_router.include_router(habits_router,     prefix="/habits",      tags=["Habits"])
api_router.include_router(coach_router,      prefix="/coach",       tags=["Coach"])
api_router.include_router(progression_router,prefix="/progression", tags=["Progression"])
