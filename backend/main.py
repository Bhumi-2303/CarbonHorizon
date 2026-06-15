"""
Carbon Horizon  —  FastAPI Application Entry Point

API prefix:  /api/v1
Docs:        /api/docs   (Swagger UI)
ReDoc:       /api/redoc
OpenAPI:     /api/openapi.json
"""
import time
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter
from app.routes import api_router

logger = logging.getLogger("app.access")

# ---------------------------------------------------------------------------
# Rate Limiter Setup
# ---------------------------------------------------------------------------
from slowapi import _rate_limit_exceeded_handler

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

app.state.limiter = limiter

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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    return response

# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = ", ".join([f"{'.'.join(str(l) for l in err['loc'])}: {err['msg']}" for err in errors])
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": msg},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal Server Error"},
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
