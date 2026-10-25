from slowapi import Limiter
from starlette.requests import Request
import jwt
from app.core.config import settings
from app.core.client_ip import get_trusted_client_ip


def get_client_identifier(request: Request = None) -> str:
    """
    Derive a rate-limiting key for the request.
    Uses Bearer token user ID if available, otherwise client IP address
    derived safely via trusted proxy resolution.
    """
    if request is None:
        return "127.0.0.1"
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        token = auth.split(" ", 1)[1].strip()
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
            sub = unverified.get("sub")
            if sub:
                return f"user:{sub}"
        except Exception:
            pass
    return get_trusted_client_ip(request)


def _get_storage_uri() -> str:
    redis_url = getattr(settings, "REDIS_URL", None)
    if redis_url:
        return redis_url
    return "memory://"


# in_memory_fallback_enabled=True ensures that when Redis is unreachable,
# rate limits continue to be enforced locally in-memory per container instance
limiter = Limiter(
    key_func=get_client_identifier,
    storage_uri=_get_storage_uri(),
    in_memory_fallback_enabled=True,
)
