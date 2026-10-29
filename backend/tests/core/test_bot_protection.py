"""
Unit tests for bot protection, Turnstile validation, honeypot traps,
and login lockout mechanisms (Task 18).
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
from app.core.login_lockout import (
    record_login_failure,
    is_locked_out,
    check_login_lockout,
    clear_login_failures,
    reset_all_lockouts,
)
from app.core.turnstile import verify_turnstile_token
from app.schemas.auth import RegisterRequest, LoginRequest
from app.schemas.coach import ChatRequest, ChatResponse


@pytest.fixture(autouse=True)
async def clean_lockouts():
    await reset_all_lockouts()
    yield
    await reset_all_lockouts()


def test_honeypot_in_register_request():
    # Empty honeypot is valid
    valid = RegisterRequest(
        full_name="Valid User",
        email="user@example.com",
        password="ValidPassword123!",
        age=25,
        honeypot="",
        terms_accepted=True,
        terms_version="2026-10-24",
    )
    assert valid.honeypot == ""

    # Non-empty honeypot triggers validation error
    with pytest.raises(ValueError, match="Bot detected via honeypot"):
        RegisterRequest(
            full_name="Bot User",
            email="bot@example.com",
            password="BotPassword123!",
            age=25,
            honeypot="I am a spam bot",
            terms_accepted=True,
            terms_version="2026-10-24",
        )


def test_honeypot_in_login_request():
    valid = LoginRequest(
        email="user@example.com",
        password="ValidPassword123!",
        honeypot=None,
    )
    assert valid.honeypot is None

    with pytest.raises(ValueError, match="Bot detected via honeypot"):
        LoginRequest(
            email="bot@example.com",
            password="BotPassword123!",
            honeypot="automated-fill",
        )


def test_honeypot_in_coach_chat_request():
    valid = ChatRequest(
        message="Hello coach",
        honeypot=None,
    )
    assert valid.message == "Hello coach"

    with pytest.raises(ValueError, match="Bot detected via honeypot"):
        ChatRequest(
            message="Spam message",
            honeypot="bot-field",
        )


@pytest.mark.asyncio
async def test_turnstile_verification_dev_and_mock_bypass():
    # In testing environment, mock token is accepted
    with patch("app.core.turnstile.settings.ENVIRONMENT", "testing"):
        res = await verify_turnstile_token(
            token="test-turnstile-token", remote_ip="127.0.0.1"
        )
        assert res is True

    # In development environment, mock token is accepted
    with patch("app.core.turnstile.settings.ENVIRONMENT", "development"):
        res = await verify_turnstile_token(
            token="test-turnstile-token", remote_ip="127.0.0.1"
        )
        assert res is True


@pytest.mark.asyncio
async def test_turnstile_production_missing_secret_key_rejects_with_500():
    # In production without a secret key, requests must fail with 500
    with patch("app.core.turnstile.settings.ENVIRONMENT", "production"), patch(
        "app.core.turnstile.settings.TURNSTILE_SECRET_KEY", None
    ):
        with pytest.raises(HTTPException) as exc_info:
            await verify_turnstile_token(
                token="any-token", remote_ip="1.2.3.4"
            )
        assert exc_info.value.status_code == 500
        assert "misconfigured" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_turnstile_production_mock_token_rejected_with_400():
    # In production, mock bypass token is strictly rejected with 400
    with patch("app.core.turnstile.settings.ENVIRONMENT", "production"), patch(
        "app.core.turnstile.settings.TURNSTILE_SECRET_KEY", "real-prod-secret"
    ):
        with pytest.raises(HTTPException) as exc_info:
            await verify_turnstile_token(
                token="test-turnstile-token", remote_ip="1.2.3.4"
            )
        assert exc_info.value.status_code == 400
        assert "Valid bot verification token is required" in exc_info.value.detail


@pytest.mark.asyncio
async def test_turnstile_verification_failure():
    # Simulate production verification failure
    with patch("app.core.turnstile.settings.ENVIRONMENT", "production"), patch(
        "app.core.turnstile.settings.TURNSTILE_SECRET_KEY", "real-secret"
    ):
        with patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {
                "success": False,
                "error-codes": ["invalid-input-response"],
            }
            mock_post.return_value = mock_resp
            with pytest.raises(
                HTTPException, match="Security verification failed"
            ):
                await verify_turnstile_token(
                    token="invalid-token", remote_ip="1.2.3.4"
                )


@pytest.mark.asyncio
async def test_login_lockout_trigger_and_recovery():
    ident = "victim@example.com"
    locked, _ = await is_locked_out(ident)
    assert locked is False

    # Record 4 failures -> not yet locked out
    for _ in range(4):
        await record_login_failure(ident)
        locked, _ = await is_locked_out(ident)
        assert locked is False

    # 5th failure triggers lockout
    await record_login_failure(ident)
    locked, remaining = await is_locked_out(ident)
    assert locked is True
    assert remaining > 0

    # check_login_lockout raises 429
    with pytest.raises(
        HTTPException, match="Too many failed login attempts"
    ) as exc_info:
        await check_login_lockout(ident)
    assert exc_info.value.status_code == 429

    # Successful login clears failures
    await clear_login_failures(ident)
    locked, _ = await is_locked_out(ident)
    assert locked is False


@pytest.mark.asyncio
async def test_redis_backed_lockout_and_expiration():
    import fakeredis.aioredis
    from app.core.redis_client import set_redis
    fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    set_redis(fake_r)
    try:
        ident = "redis_victim@example.com"
        for _ in range(5):
            await record_login_failure(ident)

        locked, remaining = await is_locked_out(ident)
        assert locked is True
        assert remaining > 0
        assert await fake_r.exists(f"lockout:blocked:{ident}") == 1

        await clear_login_failures(ident)
        locked, _ = await is_locked_out(ident)
        assert locked is False
        assert await fake_r.exists(f"lockout:blocked:{ident}") == 0
    finally:
        set_redis(None)


@pytest.mark.asyncio
async def test_login_lockout_keyed_on_account_and_ip():
    from app.core.login_lockout import make_lockout_key

    key1 = make_lockout_key("Alice@example.com", "1.2.3.4")
    key2 = make_lockout_key("Alice@example.com", "5.6.7.8")
    key3 = make_lockout_key("Bob@example.com", "1.2.3.4")

    assert key1 == "alice@example.com@1.2.3.4"
    assert key2 == "alice@example.com@5.6.7.8"
    assert key3 == "bob@example.com@1.2.3.4"

    # Trigger lockout for Alice from IP 1.2.3.4
    for _ in range(5):
        await record_login_failure(key1)

    locked1, _ = await is_locked_out(key1)
    assert locked1 is True

    # Alice from another IP is NOT locked out (no DoS of legitimate user)
    locked2, _ = await is_locked_out(key2)
    assert locked2 is False

    # Another user from the same IP is NOT locked out (no collateral lockout)
    locked3, _ = await is_locked_out(key3)
    assert locked3 is False

    await clear_login_failures(key1)


@pytest.mark.asyncio
async def test_login_lockout_fails_closed_when_redis_unreachable():
    from unittest.mock import AsyncMock
    from app.core.redis_client import set_redis

    broken_redis = AsyncMock()
    broken_redis.ttl.side_effect = Exception("Redis connection refused")
    broken_redis.incr.side_effect = Exception("Redis connection refused")
    set_redis(broken_redis)

    try:
        # In fail-closed mode, unreachable Redis must raise HTTP 503
        with pytest.raises(HTTPException) as exc_info:
            await check_login_lockout("test@user.com@1.2.3.4")
        assert exc_info.value.status_code == 503
        assert "temporarily unavailable" in exc_info.value.detail
    finally:
        set_redis(None)


def test_coach_output_xss_sanitization():
    # HTML script tags and on* event handlers are sanitized out
    malicious_output = (
        "Here are 3 tips:\n"
        "<script>alert('xss')</script>"
        "<img src=x onerror=alert(1)>"
        "1. Turn off standby power."
    )
    import uuid

    resp = ChatResponse(
        conversation_id=uuid.uuid4(),
        ai_message_id=uuid.uuid4(),
        message=malicious_output,
    )
    assert "<script>" not in resp.message
    assert "onerror=" not in resp.message
    assert "Turn off standby power." in resp.message


@pytest.mark.asyncio
async def test_account_wide_soft_threshold_and_progressive_delay():
    from app.core.login_lockout import (
        record_account_failure,
        check_account_soft_threshold,
        clear_account_failures,
        ACCOUNT_SOFT_THRESHOLD,
    )

    account = "victim@example.com"
    # Under the threshold: no delay, no turnstile required
    for _ in range(ACCOUNT_SOFT_THRESHOLD - 1):
        await record_account_failure(account)

    delay, require_turnstile = await check_account_soft_threshold(account)
    assert delay == 0.0
    assert require_turnstile is False

    # Hit threshold (20th failure)
    await record_account_failure(account)
    delay, require_turnstile = await check_account_soft_threshold(account)
    assert require_turnstile is True
    assert delay > 0.0  # Progressive delay introduced

    # Additional failures increase progressive delay up to cap (3.0s)
    for _ in range(15):
        await record_account_failure(account)
    delay_capped, require_turnstile = await check_account_soft_threshold(account)
    assert require_turnstile is True
    assert delay_capped <= 3.0

    # Successful login resets the account failure counter
    await clear_account_failures(account)
    delay_reset, require_reset = await check_account_soft_threshold(account)
    assert delay_reset == 0.0
    assert require_reset is False


@pytest.mark.asyncio
async def test_login_route_soft_threshold_requires_turnstile_token(client):
    from app.core.login_lockout import record_account_failure, ACCOUNT_SOFT_THRESHOLD

    account = "targeted_account@example.com"
    # Simulate 20 failures distributed across different IPs
    for _ in range(ACCOUNT_SOFT_THRESHOLD):
        await record_account_failure(account)

    # Attempting to login without Turnstile token now returns 403 Forbidden
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": account,
            "password": "wrongpassword",
            "turnstile_token": None,
        },
    )
    assert response.status_code == 403
    assert "Additional verification required" in response.json()["message"]


@pytest.mark.asyncio
async def test_login_route_progressive_delay_uses_asyncio_sleep(client):
    """
    Verify that asyncio.sleep is awaited with the computed progressive delay
    when an account has exceeded the soft threshold.
    """
    from unittest.mock import patch, AsyncMock
    from app.core.login_lockout import record_account_failure, ACCOUNT_SOFT_THRESHOLD

    account = "delay_test_user@example.com"
    for _ in range(ACCOUNT_SOFT_THRESHOLD):
        await record_account_failure(account)

    with patch("app.routes.auth.asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": account,
                "password": "wrongpassword",
                "turnstile_token": "test-mock-token",
            },
        )
        assert response.status_code == 401
        assert mock_sleep.called
        # Verify sleep duration is > 0
        assert mock_sleep.call_args[0][0] > 0


@pytest.mark.asyncio
async def test_account_wide_hard_ceiling_locks_account_and_dispatches_email():
    from app.core.login_lockout import (
        record_account_failure,
        is_account_hard_locked,
        check_account_hard_lockout,
        clear_account_failures,
        ACCOUNT_HARD_CEILING,
    )
    from app.services.email_service import StubEmailProvider, set_email_service

    stub = StubEmailProvider()
    set_email_service(stub)

    account = "hard_lock_victim@example.com"
    for _ in range(ACCOUNT_HARD_CEILING - 1):
        await record_account_failure(account)

    locked, _ = await is_account_hard_locked(account)
    assert locked is False
    assert len(stub.sent_emails) == 0

    # 100th failure hits hard ceiling
    await record_account_failure(account)
    locked, remaining = await is_account_hard_locked(account)
    assert locked is True
    assert remaining > 1700  # 30-minute lock

    # Enforcing check raises 429
    with pytest.raises(HTTPException) as exc_info:
        await check_account_hard_lockout(account)
    assert exc_info.value.status_code == 429
    assert "Account temporarily locked" in exc_info.value.detail

    # Email was dispatched
    assert len(stub.sent_emails) == 1
    email = stub.sent_emails[0]
    assert email["to_email"] == account
    assert "Temporarily Locked" in email["subject"]
    assert "100 failed login attempts" in email["body"]
    assert "30 minutes" in email["body"]

    # Clear account failures resets lockout
    await clear_account_failures(account)
    locked_after, _ = await is_account_hard_locked(account)
    assert locked_after is False


@pytest.mark.asyncio
async def test_login_route_account_hard_lockout_across_multiple_ips(client):
    from app.core.login_lockout import record_account_failure, ACCOUNT_HARD_CEILING
    from app.services.email_service import StubEmailProvider, set_email_service

    stub = StubEmailProvider()
    set_email_service(stub)

    account = "distributed_target@example.com"
    # Simulate 100 failures distributed across different IPs
    for _ in range(ACCOUNT_HARD_CEILING):
        await record_account_failure(account)

    # Attempt login from a fresh new IP
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": account,
            "password": "Password123!",
            "turnstile_token": "test-mock-token",
        },
        headers={"X-Forwarded-For": "198.51.100.99"},
    )
    assert response.status_code == 429
    assert "Account temporarily locked" in response.json()["message"]
    assert len(stub.sent_emails) == 1
