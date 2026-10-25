"""
Login attempt rate limiting and lockout mechanism.

Tracks repeated authentication failures per identifier (keyed on account + IP).
Also enforces an account-wide soft threshold (Turnstile challenge + delay)
and a hard account ceiling (100 failures/hour -> 30-minute lock + email notification).
Uses Redis storage when available so limits hold across distributed
Cloud Run instances. Falls back to in-memory tracking when REDIS_URL is unset.
Fails closed with HTTP 503 if Redis is unreachable in production/fail-closed mode.
"""
import time
import logging
from typing import Dict, List, Optional, Tuple
from fastapi import HTTPException, status
from app.core.redis_client import get_redis

logger = logging.getLogger("app.security")

# Default configuration: 5 failed attempts in 15m triggers 15m lockout (Account + IP)
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_SECONDS = 15 * 60  # 15 minutes
ATTEMPT_WINDOW_SECONDS = 15 * 60

# Account-wide soft threshold across all IPs (credential stuffing mitigation).
# When exceeded, mandates Turnstile verification challenge and progressive delay.
ACCOUNT_SOFT_THRESHOLD = 20
ACCOUNT_SOFT_WINDOW_SECONDS = 3600  # 1 hour

# Hard account-wide ceiling across all IPs (brute-force defense).
# Exceeding this triggers a 30-minute lock and dispatches an email notification.
ACCOUNT_HARD_CEILING = 100
ACCOUNT_HARD_LOCK_DURATION_SECONDS = 30 * 60  # 30 minutes

# In-memory storage for tracking: key -> list of failure timestamps
_failed_attempts: Dict[str, List[float]] = {}
_lockouts: Dict[str, float] = {}
_account_failures: Dict[str, List[float]] = {}
_account_hard_lockouts: Dict[str, float] = {}
_account_alerts_sent: Dict[str, float] = {}


def make_lockout_key(account: str, ip: Optional[str] = None) -> str:
    """
    Generate a composite key combining user account and client IP address.
    This prevents cross-user DoS attacks where an attacker deliberately locks
    out a legitimate user by submitting failed attempts from a different IP.
    """
    clean_account = account.strip().lower()
    clean_ip = (ip or "unknown").strip()
    return f"{clean_account}@{clean_ip}"


async def is_locked_out(identifier: str) -> Tuple[bool, int]:
    """
    Check if the given identifier (account + IP) is currently locked out.
    Uses Redis when available. Fails closed with 503 if Redis is unreachable
    and REDIS_FAIL_OPEN is False.
    Returns (is_locked, remaining_seconds).
    """
    r = get_redis()
    if r is not None:
        try:
            lock_key = f"lockout:blocked:{identifier}"
            ttl = await r.ttl(lock_key)
            if ttl > 0:
                return True, ttl
            return False, 0
        except Exception as e:
            logger.error(
                f"Redis lockout check failed: {e}"
            )
            from app.core.config import settings
            if not getattr(settings, "REDIS_FAIL_OPEN", False):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "Authentication security service temporarily "
                        "unavailable. Please try again shortly."
                    ),
                )
            logger.warning("Failing open to in-memory lockout tracker")

    now = time.time()
    if identifier in _lockouts:
        expiry = _lockouts[identifier]
        if now < expiry:
            remaining = int(expiry - now)
            return True, remaining
        else:
            del _lockouts[identifier]
            _failed_attempts.pop(identifier, None)

    return False, 0


async def is_account_hard_locked(account: str) -> Tuple[bool, int]:
    """
    Check if the account is currently under account-wide hard lockout (30m).
    Returns (is_locked, remaining_seconds).
    """
    clean_account = account.strip().lower()
    r = get_redis()
    if r is not None:
        try:
            lock_key = f"lockout:account_hard_blocked:{clean_account}"
            ttl = await r.ttl(lock_key)
            if ttl > 0:
                return True, ttl
            return False, 0
        except Exception as e:
            logger.error(f"Redis account hard lockout check failed: {e}")
            from app.core.config import settings
            if not getattr(settings, "REDIS_FAIL_OPEN", False):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "Authentication security service temporarily "
                        "unavailable. Please try again shortly."
                    ),
                )
            logger.warning("Failing open to in-memory account hard lock tracker")

    now = time.time()
    if clean_account in _account_hard_lockouts:
        expiry = _account_hard_lockouts[clean_account]
        if now < expiry:
            remaining = int(expiry - now)
            return True, remaining
        else:
            del _account_hard_lockouts[clean_account]

    return False, 0


async def record_login_failure(identifier: str) -> None:
    """
    Record an authentication failure for the given identifier (account + IP).
    Uses Redis when available; fails closed with 503 if Redis is unreachable
    and REDIS_FAIL_OPEN is False.
    """
    r = get_redis()
    if r is not None:
        try:
            failed_key = f"lockout:failed:{identifier}"
            count = await r.incr(failed_key)
            if count == 1:
                await r.expire(failed_key, ATTEMPT_WINDOW_SECONDS)
            if count >= MAX_FAILED_ATTEMPTS:
                lock_key = f"lockout:blocked:{identifier}"
                await r.set(lock_key, "1", ex=LOCKOUT_DURATION_SECONDS)
            return
        except Exception as e:
            logger.error(
                f"Redis record failure failed: {e}"
            )
            from app.core.config import settings
            if not getattr(settings, "REDIS_FAIL_OPEN", False):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "Authentication security service temporarily "
                        "unavailable."
                    ),
                )
            logger.warning("Failing open to in-memory failure recorder")

    now = time.time()
    cutoff = now - ATTEMPT_WINDOW_SECONDS
    attempts = _failed_attempts.get(identifier, [])
    attempts = [t for t in attempts if t > cutoff]
    attempts.append(now)
    _failed_attempts[identifier] = attempts

    if len(attempts) >= MAX_FAILED_ATTEMPTS:
        _lockouts[identifier] = now + LOCKOUT_DURATION_SECONDS


async def clear_login_failures(identifier: str) -> None:
    """Clear failure history upon successful authentication."""
    r = get_redis()
    if r is not None:
        try:
            await r.delete(
                f"lockout:failed:{identifier}",
                f"lockout:blocked:{identifier}",
            )
        except Exception as e:
            logger.warning(f"Redis clear failures failed: {e}")

    _failed_attempts.pop(identifier, None)
    _lockouts.pop(identifier, None)


async def _trigger_account_hard_lock(account: str) -> None:
    """Trigger the 30-minute account lock and dispatch security alert email."""
    from app.services.email_service import get_email_service
    from app.db.session import SessionLocal
    from app.models.user import User
    from sqlalchemy import func

    clean_account = account.strip().lower()

    # Query if account exists in DB before dispatching real security email
    # to avoid emailing arbitrary addresses.
    try:
        with SessionLocal() as db:
            user = (
                db.query(User)
                .filter(
                    func.lower(User.email) == clean_account,
                    User.deleted_at.is_(None),
                )
                .first()
            )
            if not user:
                logger.info(
                    "Account hard lock for unregistered email %s; skipping email",
                    clean_account,
                )
                return
    except Exception as e:
        logger.warning(f"Could not query user for lockout alert email: {e}")

    subject = "Security Alert: Carbon Horizon Account Temporarily Locked"
    body = (
        f"We detected more than {ACCOUNT_HARD_CEILING} failed login attempts for your "
        f"account ({clean_account}) within the past hour across multiple locations. "
        f"For your security, your account has been temporarily locked for "
        f"{ACCOUNT_HARD_LOCK_DURATION_SECONDS // 60} minutes.\n\n"
        f"If this was not you, someone may be attempting to access your account. "
        f"Please ensure your password is secure and review your account activity."
    )
    email_service = get_email_service()
    try:
        await email_service.send_security_alert_email(clean_account, subject, body)
    except Exception as e:
        logger.error(f"Failed to dispatch security alert email: {e}")


async def record_account_failure(account: str) -> None:
    """
    Record an authentication failure for the account across all IPs.
    Checks soft threshold and hard account ceiling (100 attempts -> 30m lock + email).
    Ensures at most one security alert email is dispatched per lockout period.
    """
    clean_account = account.strip().lower()
    r = get_redis()
    if r is not None:
        try:
            failed_key = f"lockout:account_failed:{clean_account}"
            count = await r.incr(failed_key)
            if count == 1:
                await r.expire(failed_key, ACCOUNT_SOFT_WINDOW_SECONDS)
            if count >= ACCOUNT_HARD_CEILING:
                hard_lock_key = f"lockout:account_hard_blocked:{clean_account}"
                await r.set(
                    hard_lock_key, "1", ex=ACCOUNT_HARD_LOCK_DURATION_SECONDS
                )
                # Atomically set alert key with NX=True so exactly one alert is sent
                alert_key = f"lockout:account_alert_sent:{clean_account}"
                dispatched = await r.set(
                    alert_key,
                    "1",
                    ex=ACCOUNT_HARD_LOCK_DURATION_SECONDS,
                    nx=True,
                )
                if dispatched:
                    await _trigger_account_hard_lock(clean_account)
            return
        except Exception as e:
            logger.error(f"Redis record account failure failed: {e}")
            from app.core.config import settings
            if not getattr(settings, "REDIS_FAIL_OPEN", False):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication security service temporarily unavailable.",
                )
            logger.warning("Failing open to in-memory account failure recorder")

    now = time.time()
    cutoff = now - ACCOUNT_SOFT_WINDOW_SECONDS
    attempts = _account_failures.get(clean_account, [])
    attempts = [t for t in attempts if t > cutoff]
    attempts.append(now)
    _account_failures[clean_account] = attempts

    if len(attempts) >= ACCOUNT_HARD_CEILING:
        _account_hard_lockouts[clean_account] = (
            now + ACCOUNT_HARD_LOCK_DURATION_SECONDS
        )
        alert_until = _account_alerts_sent.get(clean_account, 0)
        if now >= alert_until:
            _account_alerts_sent[clean_account] = (
                now + ACCOUNT_HARD_LOCK_DURATION_SECONDS
            )
            await _trigger_account_hard_lock(clean_account)


async def check_account_soft_threshold(account: str) -> Tuple[float, bool]:
    """
    Check if the account has exceeded the soft failure threshold across all IPs.
    Returns (progressive_delay_seconds, require_turnstile).
    """
    clean_account = account.strip().lower()
    count = 0
    r = get_redis()
    if r is not None:
        try:
            val = await r.get(f"lockout:account_failed:{clean_account}")
            if val is not None:
                count = int(val)
        except Exception as e:
            logger.error(f"Redis check account soft threshold failed: {e}")
            from app.core.config import settings
            if not getattr(settings, "REDIS_FAIL_OPEN", False):
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=(
                        "Authentication security service temporarily "
                        "unavailable. Please try again shortly."
                    ),
                )
    else:
        now = time.time()
        cutoff = now - ACCOUNT_SOFT_WINDOW_SECONDS
        attempts = [
            t for t in _account_failures.get(clean_account, []) if t > cutoff
        ]
        _account_failures[clean_account] = attempts
        count = len(attempts)

    if count >= ACCOUNT_SOFT_THRESHOLD:
        excess = count - ACCOUNT_SOFT_THRESHOLD + 1
        delay = min(3.0, 0.25 * excess)
        return delay, True

    return 0.0, False


async def clear_account_failures(account: str) -> None:
    """Clear account-wide failure count upon successful authentication."""
    clean_account = account.strip().lower()
    r = get_redis()
    if r is not None:
        try:
            await r.delete(
                f"lockout:account_failed:{clean_account}",
                f"lockout:account_hard_blocked:{clean_account}",
            )
        except Exception as e:
            logger.warning(f"Redis clear account failures failed: {e}")

    _account_failures.pop(clean_account, None)
    _account_hard_lockouts.pop(clean_account, None)
    _account_alerts_sent.pop(clean_account, None)


async def check_login_lockout(identifier: str) -> None:
    """
    Enforce lockout check for composite account+IP. Raises HTTPException(429)
    if the account on this specific IP is locked out.
    """
    locked, remaining_sec = await is_locked_out(identifier)
    if locked:
        minutes = max(1, remaining_sec // 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Too many failed login attempts. For security, please wait "
                f"{minutes} minute(s) before trying again."
            ),
        )


async def check_account_hard_lockout(account: str) -> None:
    """
    Enforce hard account-wide ceiling check. Raises HTTPException(429)
    if the account has exceeded 100 failed attempts across all IPs.
    """
    locked, remaining_sec = await is_account_hard_locked(account)
    if locked:
        minutes = max(1, remaining_sec // 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Account temporarily locked due to excessive failed attempts. "
                f"Please wait {minutes} minute(s) before trying again or check your "
                f"email for security instructions."
            ),
        )


async def reset_all_lockouts() -> None:
    """Helper for test suites to clear lockout state."""
    _failed_attempts.clear()
    _lockouts.clear()
    _account_failures.clear()
    _account_hard_lockouts.clear()
    _account_alerts_sent.clear()
    r = get_redis()
    if r is not None:
        try:
            keys = await r.keys("lockout:*")
            if keys:
                await r.delete(*keys)
        except Exception:
            pass
