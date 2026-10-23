"""
tests/auth/test_token_revocation.py
====================================
Comprehensive tests for Redis-backed token revocation, JTI blocklist,
refresh token rotation, and get_current_user middleware integration.

Using fakeredis to simulate Redis behavior without requiring a running server.
"""
from __future__ import annotations

import time
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
import jwt
import fakeredis.aioredis

from app.core.config import settings
from app.core.redis_client import set_redis, get_redis
import app.core.redis_client as rc
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user,
    is_token_revoked,
    revoke_token,
    revoke_all_user_tokens,
)
from app.services import auth_service
from app.schemas.auth import RefreshRequest, LogoutRequest

# Mark all tests in this module as asyncio tests
pytestmark = pytest.mark.asyncio

@pytest.fixture(autouse=True)
def setup_fake_redis():
    """Fixture to set up and tear down a fake Redis instance for every test."""
    fake_r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    set_redis(fake_r)
    yield fake_r
    set_redis(None)

class TestJTIBlocklist:
    async def test_non_revoked_token_passes(self, db, make_user):
        user = make_user()
        token = create_access_token(subject=str(user.id))
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Checking if get_current_user succeeds
        retrieved_user = await get_current_user(creds, db)
        assert retrieved_user.id == user.id

    async def test_revoked_token_raises_401(self, db, make_user, setup_fake_redis):
        user = make_user()
        token = create_access_token(subject=str(user.id))
        claims = decode_token(token)
        jti = claims["jti"]

        # Revoke the token
        await revoke_token(jti, ttl_seconds=100)

        # Verify it is revoked
        assert await is_token_revoked(jti) is True

        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(creds, db)
        assert exc_info.value.status_code == 401
        assert "revoked" in exc_info.value.detail

    async def test_legacy_token_without_jti_passes(self, db, make_user):
        user = make_user()
        # Create token manually without JTI claim
        payload = {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
            "type": "access",
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

        # Verify it passes
        retrieved_user = await get_current_user(creds, db)
        assert retrieved_user.id == user.id

class TestLogoutFlows:
    async def test_logout_revokes_access_token(self, setup_fake_redis, db, make_user):
        user = make_user()
        # Login to generate token response
        token_resp = await auth_service.login_user(db, user.email, "TestPass123!")

        claims = decode_token(token_resp.access_token)
        jti = claims["jti"]

        # Perform logout
        await auth_service.logout(
            access_token_claims=claims,
            refresh_token=None,
            user_id=str(user.id)
        )

        # Should be blocklisted
        assert await is_token_revoked(jti) is True

        # TTL should be set correctly (approx ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        ttl = await setup_fake_redis.ttl(f"revoked_token:{jti}")
        assert 0 < ttl <= settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    async def test_logout_with_refresh_token(self, setup_fake_redis, db, make_user):
        user = make_user()
        token_resp = await auth_service.login_user(db, user.email, "TestPass123!")

        access_claims = decode_token(token_resp.access_token)
        refresh_claims = decode_token(token_resp.refresh_token)

        # Perform logout with refresh token too
        await auth_service.logout(
            access_token_claims=access_claims,
            refresh_token=token_resp.refresh_token,
            user_id=str(user.id)
        )

        assert await is_token_revoked(access_claims["jti"]) is True
        assert await is_token_revoked(refresh_claims["jti"]) is True

    async def test_logout_expired_refresh_token_graceful(self, setup_fake_redis, db, make_user):
        user = make_user()
        token_resp = await auth_service.login_user(db, user.email, "TestPass123!")
        access_claims = decode_token(token_resp.access_token)

        # Create an expired refresh token manually
        expired_payload = {
            "sub": str(user.id),
            "exp": datetime.now(timezone.utc) - timedelta(seconds=10),
            "type": "refresh",
            "jti": "some-jti"
        }
        expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        # Should not crash
        await auth_service.logout(
            access_token_claims=access_claims,
            refresh_token=expired_token,
            user_id=str(user.id)
        )
        assert await is_token_revoked(access_claims["jti"]) is True

    async def test_logout_all_revokes_all_sessions(self, setup_fake_redis, db, make_user):
        user = make_user()

        # Simulate logging in twice
        resp1 = await auth_service.login_user(db, user.email, "TestPass123!")
        resp2 = await auth_service.login_user(db, user.email, "TestPass123!")

        claims1 = decode_token(resp1.access_token)
        claims2 = decode_token(resp2.access_token)

        # Revoke all user tokens
        revoked_count = await auth_service.logout_all(str(user.id))
        assert revoked_count == 4  # 2 access tokens + 2 refresh tokens

        assert await is_token_revoked(claims1["jti"]) is True
        assert await is_token_revoked(claims2["jti"]) is True

class TestRefreshTokenRotation:
    async def test_refresh_token_rotation_and_revocation(self, setup_fake_redis, db, make_user):
        user = make_user()
        token_resp = await auth_service.login_user(db, user.email, "TestPass123!")

        old_refresh_claims = decode_token(token_resp.refresh_token)
        old_refresh_jti = old_refresh_claims["jti"]

        # Rotate refresh token
        req = RefreshRequest(refresh_token=token_resp.refresh_token)
        new_resp = await auth_service.refresh_tokens(db, req)

        # Old refresh token must be revoked
        assert await is_token_revoked(old_refresh_jti) is True

        # New refresh token must be valid and different
        new_refresh_claims = decode_token(new_resp.refresh_token)
        assert new_refresh_claims["jti"] != old_refresh_jti

        # Attempt to reuse old refresh token must fail with 401
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.refresh_tokens(db, req)
        assert exc_info.value.status_code == 401
        assert "Session expired" in exc_info.value.detail

class TestRedisFailPolicies:
    async def test_fail_closed_policy_default(self, db, make_user):
        # Set REDIS_FAIL_OPEN to False
        with patch("app.core.security.settings.REDIS_FAIL_OPEN", False):
            # Mock get_redis to return a client that raises connection error
            mock_client = MagicMock()

            # Since is_token_revoked is async, its call to exists must be awaited.
            # We mock the exists method as an async function.
            async def mock_exists(*args, **kwargs):
                raise Exception("Redis Connection Refused")
            mock_client.exists = mock_exists

            with patch("app.core.redis_client.get_redis", return_value=mock_client):
                user = make_user()
                token = create_access_token(subject=str(user.id))
                creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

                # Should raise 503 Service Unavailable
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(creds, db)
                assert exc_info.value.status_code == 503
                assert "Authentication service temporarily unavailable" in exc_info.value.detail

    async def test_fail_open_policy(self, db, make_user):
        # Set REDIS_FAIL_OPEN to True
        with patch("app.core.security.settings.REDIS_FAIL_OPEN", True):
            # Mock get_redis to return a client that raises connection error
            mock_client = MagicMock()

            async def mock_exists(*args, **kwargs):
                raise Exception("Redis Connection Refused")
            mock_client.exists = mock_exists

            with patch("app.core.redis_client.get_redis", return_value=mock_client):
                user = make_user()
                token = create_access_token(subject=str(user.id))
                creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

                # Should proceed and succeed
                retrieved_user = await get_current_user(creds, db)
                assert retrieved_user.id == user.id

class TestEndpointIntegration:
    async def test_full_integration_flow(self, client, db, test_user):
        # 1. Login
        login_payload = {"email": test_user.email, "password": "GoodPass42!"}
        resp = client.post("/api/v1/auth/login", json=login_payload)
        assert resp.status_code == 200
        data = resp.json()["data"]
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # 2. Access protected endpoint (e.g. GET /profile)
        headers = {"Authorization": f"Bearer {access_token}"}
        profile_resp = client.get("/api/v1/auth/profile", headers=headers)
        assert profile_resp.status_code == 200

        # 3. Logout
        logout_payload = {"refresh_token": refresh_token}
        logout_resp = client.post("/api/v1/auth/logout", json=logout_payload, headers=headers)
        assert logout_resp.status_code == 200

        # 4. Try accessing protected endpoint again -> should fail with 401
        profile_resp2 = client.get("/api/v1/auth/profile", headers=headers)
        assert profile_resp2.status_code == 401

        # 5. Try using refresh token -> should fail with 401
        refresh_payload = {"refresh_token": refresh_token}
        refresh_resp = client.post("/api/v1/auth/refresh", json=refresh_payload)
        assert refresh_resp.status_code == 401

    async def test_deactivate_account_revokes_sessions(self, client, test_user):
        # 1. Login
        login_payload = {"email": test_user.email, "password": "GoodPass42!"}
        resp = client.post("/api/v1/auth/login", json=login_payload)
        assert resp.status_code == 200
        access_token = resp.json()["data"]["access_token"]

        # 2. Deactivate account
        headers = {"Authorization": f"Bearer {access_token}"}
        delete_resp = client.delete("/api/v1/auth/account", headers=headers)
        assert delete_resp.status_code == 204

        # 3. Requesting again with same token should fail with 401 because session was revoked
        profile_resp = client.get("/api/v1/auth/profile", headers=headers)
        assert profile_resp.status_code == 401

class TestLatencyBenchmark:
    async def test_exists_check_latency(self, setup_fake_redis):
        # Benchmark the speed of is_token_revoked which does EXISTS check
        jti = "benchmark-jti-uuid"

        start_time = time.perf_counter()
        iterations = 1000
        for _ in range(iterations):
            await is_token_revoked(jti)
        end_time = time.perf_counter()

        avg_latency_ms = ((end_time - start_time) / iterations) * 1000
        print(f"\nAverage Redis EXISTS check latency: {avg_latency_ms:.4f} ms")
        assert avg_latency_ms < 5.0  # Must be sub-millisecond to single-digit millisecond
