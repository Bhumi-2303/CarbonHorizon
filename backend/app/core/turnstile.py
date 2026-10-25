"""
Cloudflare Turnstile bot verification service.

Validates Turnstile response tokens server-side to protect sensitive endpoints
(signup, login, AI coach) from bot abuse and automated credential stuffing.
"""
import logging
from typing import Optional
import httpx
from fastapi import HTTPException, status
from app.core.config import settings

logger = logging.getLogger("app.security")

TURNSTILE_VERIFY_URL = (
    "https://challenges.cloudflare.com/turnstile/v0/siteverify"
)


async def verify_turnstile_token(
    token: Optional[str],
    remote_ip: Optional[str] = None,
) -> bool:
    """
    Verify Cloudflare Turnstile token server-side.

    Mock bypass is active ONLY when ENVIRONMENT is 'development' or 'testing'.
    In any other environment (e.g. production, staging):
    - A missing TURNSTILE_SECRET_KEY rejects requests with HTTP 500.
    - Mock tokens ('test-turnstile-token') are rejected with HTTP 400.
    - Real token is validated against Cloudflare siteverify API.
    """
    secret_key = getattr(settings, "TURNSTILE_SECRET_KEY", None)
    is_dev_or_test = settings.ENVIRONMENT in ("development", "testing")

    if is_dev_or_test:
        if token == "test-turnstile-token" or not secret_key or not token:
            return True

    # In production/staging, missing secret key must reject requests
    if not secret_key:
        logger.error(
            "TURNSTILE_SECRET_KEY missing in %s environment",
            settings.ENVIRONMENT,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Bot verification service is misconfigured.",
        )

    # In production/staging, mock tokens and empty tokens are rejected
    if not token or token == "test-turnstile-token":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Valid bot verification token is required.",
        )

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            payload = {
                "secret": secret_key,
                "response": token,
            }
            if remote_ip:
                payload["remoteip"] = remote_ip

            response = await client.post(TURNSTILE_VERIFY_URL, data=payload)
            data = response.json()

            if not data.get("success"):
                logger.warning(
                    f"Turnstile verification failed: {data.get('error-codes')}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Security verification failed. Please try again.",
                )
            return True
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during Turnstile verification: {e}")
        if settings.ENVIRONMENT == "production":
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Verification service temporarily unavailable.",
            )
        return False
