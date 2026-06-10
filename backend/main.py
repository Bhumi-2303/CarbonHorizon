"""
Carbon Horizon  —  FastAPI Application Entry Point

API prefix:  /api/v1
Docs:        /api/docs   (Swagger UI)
ReDoc:       /api/redoc
OpenAPI:     /api/openapi.json
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes import api_router

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Carbon Horizon API — Track your carbon footprint, simulate reductions, "
        "forecast emissions, manage sustainability goals, log eco-habits, and "
        "chat with an AI climate coach."
    ),
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    # Group tags appear in this order in Swagger UI
    openapi_tags=[
        {"name": "Auth",       "description": "Registration, login, token management"},
        {"name": "Assessment", "description": "Carbon footprint assessments"},
        {"name": "Dashboard",  "description": "Aggregated stats and history for the dashboard"},
        {"name": "Simulator",  "description": "What-if emission reduction scenarios"},
        {"name": "Forecast",   "description": "Emission trajectory forecasts"},
        {"name": "Goals",      "description": "Sustainability goal tracking"},
        {"name": "Habits",     "description": "Daily eco-habit logging"},
        {"name": "Coach",      "description": "AI climate coach chat"},
        {"name": "Health",     "description": "Service health probes"},
    ],
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

app.include_router(api_router, prefix=settings.API_V1_STR)

# ---------------------------------------------------------------------------
# Health probes
# ---------------------------------------------------------------------------


@app.get("/", tags=["Health"], summary="Root — service identity")
async def root():
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "healthy",
        "docs": "/api/docs",
    }


@app.get("/health", tags=["Health"], summary="Liveness probe")
async def health_check():
    return {"status": "ok"}
