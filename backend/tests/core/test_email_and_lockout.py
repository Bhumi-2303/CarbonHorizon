"""
Tests for EmailProvider implementations, one-per-lock email throttling,
and timing/response equivalence between existing and non-existing accounts.
"""
import time
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.login_lockout import (
    ACCOUNT_HARD_CEILING,
    record_account_failure,
    reset_all_lockouts,
)
from app.core.security import hash_password
from app.models.user import User
from app.services.auth_service import login_user
from app.services.email_service import (
    ResendEmailProvider,
    SMTPEmailProvider,
    StubEmailProvider,
    set_email_service,
)


@pytest.mark.asyncio
async def test_resend_email_provider_success():
    """Verify ResendEmailProvider sends JSON payload to Resend API endpoint."""
    provider = ResendEmailProvider(
        api_key="re_mock_test_key",
        from_email="alerts@carbonhorizon.app",
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "msg_12345"}

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        success = await provider.send_security_alert_email(
            "user@carbonhorizon.app",
            "Security Alert",
            "Your account was locked."
        )
        assert success is True
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert args[0] == "https://api.resend.com/emails"
        assert kwargs["headers"]["Authorization"] == "Bearer re_mock_test_key"
        assert kwargs["json"]["to"] == ["user@carbonhorizon.app"]


@pytest.mark.asyncio
async def test_smtp_email_provider_success():
    """Verify SMTPEmailProvider initiates SMTP session and dispatches message."""
    provider = SMTPEmailProvider(
        host="smtp.testserver.com",
        port=587,
        user="testuser",
        password="testpassword",
        use_tls=True,
        from_email="security@carbonhorizon.app"
    )

    with patch("smtplib.SMTP") as mock_smtp_class:
        mock_smtp = MagicMock()
        mock_smtp_class.return_value = mock_smtp

        success = await provider.send_security_alert_email(
            "user@carbonhorizon.app",
            "Security Alert",
            "Your account was locked."
        )
        assert success is True
        mock_smtp.starttls.assert_called_once()
        mock_smtp.login.assert_called_once_with("testuser", "testpassword")
        mock_smtp.sendmail.assert_called_once()


@pytest.mark.asyncio
async def test_lock_alerts_limited_to_one_per_lock_window(db: Session):
    """
    Ensure only ONE email is sent when the account-wide hard ceiling is exceeded,
    even if further login failures occur while the account remains locked.
    """
    await reset_all_lockouts()
    stub = StubEmailProvider()
    set_email_service(stub)

    target_email = "real_existing_user@carbonhorizon.app"
    # Seed user in DB so _trigger_account_hard_lock allows email dispatch
    user = User(
        email=target_email,
        full_name="Target User",
        password_hash=hash_password("ValidPassword123!"),
    )
    db.add(user)
    db.commit()

    try:
        # Trigger failures up to the 100 threshold
        for _ in range(ACCOUNT_HARD_CEILING):
            await record_account_failure(target_email)

        assert len(stub.sent_emails) == 1
        assert stub.sent_emails[0]["to_email"] == target_email

        # Exceed ceiling further (attempts 101, 102, 103)
        for _ in range(10):
            await record_account_failure(target_email)

        # Still exactly ONE email sent!
        assert len(stub.sent_emails) == 1
    finally:
        await reset_all_lockouts()
        set_email_service(None)


@pytest.mark.asyncio
async def test_login_response_and_timing_equivalence(db: Session):
    """
    Assert that response status, error detail, and execution timing are identical
    between existing and non-existing accounts, defending against username enumeration.
    """
    existing_email = "known_valid_account@carbonhorizon.app"
    user = User(
        email=existing_email,
        full_name="Known User",
        password_hash=hash_password("RealPassword123!"),
    )
    db.add(user)
    db.commit()

    non_existing_email = "unknown_random_account@carbonhorizon.app"

    # 1. Existing account with invalid password
    t0 = time.perf_counter()
    with pytest.raises(HTTPException) as exc_existing:
        await login_user(db, existing_email, "WrongPassword123!")
    existing_duration = time.perf_counter() - t0

    # 2. Non-existing account with arbitrary password
    t1 = time.perf_counter()
    with pytest.raises(HTTPException) as exc_non_existing:
        await login_user(db, non_existing_email, "WrongPassword123!")
    non_existing_duration = time.perf_counter() - t1

    # Status codes and details must be strictly identical
    assert exc_existing.value.status_code == 401
    assert exc_non_existing.value.status_code == 401
    assert exc_existing.value.detail == exc_non_existing.value.detail
    expected_msg = "We couldn't sign you in. Please check your email and password."
    assert exc_existing.value.detail == expected_msg

    # Both run bcrypt verification (~100-300ms) - timing delta must be small
    timing_delta = abs(existing_duration - non_existing_duration)
    msg = (
        f"Timing difference too high: {timing_delta:.4f}s "
        f"(existing: {existing_duration:.4f}s, "
        f"non_existing: {non_existing_duration:.4f}s)"
    )
    assert timing_delta < 0.25, msg
