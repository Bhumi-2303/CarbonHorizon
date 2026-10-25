"""
Carbon Horizon  —  FastAPI Application Entry Point

API prefix:  /api/v1
Docs:        /api/docs   (Swagger UI)
ReDoc:       /api/redoc
OpenAPI:     /api/openapi.json
"""
import time
import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.rate_limit import limiter
from app.routes import api_router

logger = logging.getLogger("app.access")

# ---------------------------------------------------------------------------
# App factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Carbon Horizon API — Track your carbon footprint, "
        "simulate reductions, forecast emissions, manage sustainability "
        "goals, log eco-habits, and chat with an AI climate coach."
    ),
    docs_url=None if settings.ENVIRONMENT == "production" else "/api/docs",
    redoc_url=None if settings.ENVIRONMENT == "production" else "/api/redoc",
    openapi_url=None if settings.ENVIRONMENT == "production" else "/api/openapi.json",
    # Group tags appear in this order in Swagger UI
    openapi_tags=[
        {"name": "Auth", "description": "Registration, login, tokens"},
        {"name": "Assessment", "description": "Carbon footprint assessments"},
        {"name": "Dashboard", "description": "Dashboard statistics"},
        {"name": "Simulator", "description": "Reduction scenarios"},
        {"name": "Forecast", "description": "Emission trajectory forecasts"},
        {"name": "Goals", "description": "Sustainability goal tracking"},
        {"name": "Habits", "description": "Daily eco-habit logging"},
        {"name": "Coach", "description": "AI climate coach chat"},
        {"name": "Health", "description": "Service health probes"},
    ],
)

app.state.limiter = limiter


@app.on_event("startup")
async def startup_event():
    from urllib.parse import urlparse
    from app.core.redis_client import init_redis

    logger.info(f"ENVIRONMENT: {settings.ENVIRONMENT}")

    # Validate SECRET_KEY for production
    if settings.ENVIRONMENT == "production":
        default_keys = [
            "change-me-in-production-use-32-char-minimum",
            "change-me-use-a-32-char-random-hex-string"
        ]
        if not settings.SECRET_KEY or settings.SECRET_KEY in default_keys:
            logger.error(
                "FATAL: Cannot start production server without valid key"
            )
            raise ValueError(
                "SECRET_KEY must be provided and cannot be a default value "
                "in production"
            )

        if not settings.REDIS_URL:
            logger.critical(
                "FATAL: REDIS_URL must be configured in production"
            )
            raise ValueError(
                "REDIS_URL must be provided and cannot be empty in production"
            )

        if not settings.ALLOWED_ORIGINS:
            logger.critical("FATAL: ALLOWED_ORIGINS must be configured in production")
            raise ValueError(
                "ALLOWED_ORIGINS must be configured and non-empty in production"
            )

        for origin in settings.ALLOWED_ORIGINS:
            if "localhost" in origin.lower() or "127.0.0.1" in origin or origin == "*":
                logger.critical(
                    f"FATAL: Insecure origin '{origin}' not permitted in "
                    "production ALLOWED_ORIGINS"
                )
                raise ValueError(
                    f"Insecure origin '{origin}' is not permitted in "
                    "production ALLOWED_ORIGINS"
                )

        # Validate Email Provider configuration for production
        email_prov = getattr(settings, "EMAIL_PROVIDER", "").lower().strip()
        if email_prov in ("stub", "console"):
            logger.critical(
                "FATAL: EMAIL_PROVIDER cannot be 'stub' or 'console' in production"
            )
            raise ValueError(
                "EMAIL_PROVIDER cannot be 'stub' or 'console' in production. "
                "Must be configured with a real provider ('resend' or 'smtp')."
            )

        if email_prov == "resend":
            if not getattr(settings, "RESEND_API_KEY", None):
                logger.critical(
                    "FATAL: RESEND_API_KEY must be configured in production"
                )
                raise ValueError(
                    "RESEND_API_KEY secret must be configured in production "
                    "when using resend."
                )
        elif email_prov == "smtp":
            if not getattr(settings, "SMTP_HOST", None) or not getattr(
                settings, "SMTP_PASSWORD", None
            ):
                logger.critical(
                    "FATAL: SMTP_HOST and SMTP_PASSWORD must be set in production"
                )
                raise ValueError(
                    "SMTP_HOST and SMTP_PASSWORD secret must be configured "
                    "in production when using smtp."
                )
        else:
            logger.critical(
                f"FATAL: Unsupported production EMAIL_PROVIDER '{email_prov}'"
            )
            raise ValueError(
                f"Unsupported production EMAIL_PROVIDER '{email_prov}'"
            )

    parsed = urlparse(settings.DATABASE_URL)
    engine = parsed.scheme
    host = parsed.hostname or "local"

    logger.info(f"DB Engine: {engine}")
    logger.info(f"DB Host: {host}")

    # Initialize Redis connection pool for token revocation
    await init_redis()


@app.on_event("shutdown")
async def shutdown_event():
    from app.core.redis_client import close_redis
    await close_redis()
    logger.info("Application shutdown complete")


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
async def enforce_https_redirect(request: Request, call_next):
    """
    Redirect HTTP to HTTPS by honoring the X-Forwarded-Proto header sent by
    Cloud Run / reverse proxies, without blindly trusting the local scheme.
    """
    proto = request.headers.get("x-forwarded-proto", "").lower().strip()
    if proto == "http":
        target_url = request.url.replace(scheme="https")
        return RedirectResponse(
            url=str(target_url),
            status_code=status.HTTP_308_PERMANENT_REDIRECT,
        )
    return await call_next(request)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """
    Inject comprehensive security headers on all outgoing HTTP responses.
    """
    response = await call_next(request)
    headers = response.headers
    headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    headers["X-Content-Type-Options"] = "nosniff"
    headers["X-Frame-Options"] = "DENY"
    headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' https://challenges.cloudflare.com https://plausible.io; "
        "frame-src 'self' https://challenges.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data:; "
        "connect-src 'self' https://challenges.cloudflare.com https://plausible.io; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "frame-ancestors 'none';"
    )
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.4f}s"
    )
    return response


# ---------------------------------------------------------------------------
# Exception Handlers
# ---------------------------------------------------------------------------

app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.detail},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    errors = exc.errors()
    msg = ", ".join(
        [
            f"{'.'.join(str(part) for part in err['loc'])}: {err['msg']}"
            for err in errors
        ]
    )
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
