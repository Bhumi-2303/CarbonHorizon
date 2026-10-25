"""
Tests for rate limiter and auth lockout behavior when Redis errors.

Verifies:
1. in_memory_fallback_enabled=True ensures that when Redis is down, rate limits
   continue to be enforced locally in-memory per container instance.
2. /api/v1/auth/register (limit: 5/minute) rejects excessive requests with HTTP 429
   even when Redis is unreachable.
3. /api/v1/coach/chat (limit: 20/minute) rejects excessive requests with HTTP 429
   even when Redis is unreachable.
4. Auth routes fail closed (return HTTP 503) when Redis fails during lockout checks.
"""
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.redis_client import set_redis
from app.core.rate_limit import limiter


def test_auth_route_fails_closed_when_redis_errors(client):
    broken_redis = AsyncMock()
    broken_redis.ttl.side_effect = Exception("Redis connection refused")
    broken_redis.incr.side_effect = Exception("Redis connection refused")
    broken_redis.get.side_effect = Exception("Redis connection refused")
    set_redis(broken_redis)

    try:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "Password123!",
                "turnstile_token": "dummy-token",
            },
        )
        # Auth routes must fail closed (503 Service Unavailable)
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["message"]
    finally:
        set_redis(None)


def test_limiter_in_memory_fallback_configuration():
    # Assert that limiter has in_memory_fallback_enabled configured
    assert limiter._in_memory_fallback_enabled is True
    assert limiter._fallback_storage is not None
    assert limiter._fallback_limiter is not None


def test_auth_register_rate_limited_when_redis_down(client, db):
    """
    Verify that /api/v1/auth/register (5/minute) continues to enforce rate limits
    using the in-memory fallback when Redis is dead.
    """
    prev_enabled = limiter.enabled
    prev_hit = limiter._limiter.hit
    prev_check = limiter._storage.check

    limiter.enabled = True
    # Simulate Redis connection failure on primary storage
    limiter._limiter.hit = MagicMock(side_effect=Exception("Redis connection lost"))
    limiter._storage.check = MagicMock(return_value=False)
    limiter.reset()

    try:
        statuses = []
        for i in range(6):
            payload = {
                "email": f"ratelimit_reg_{i}@example.com",
                "password": "Password123!",
                "full_name": f"User {i}",
                "terms_accepted": True,
                "terms_version": "1.0",
                "turnstile_token": "test-mock-token",
            }
            res = client.post("/api/v1/auth/register", json=payload)
            statuses.append(res.status_code)

        # First 5 succeed (201 Created), 6th must be rejected with 429
        assert statuses[:5] == [201] * 5
        assert statuses[5] == 429
    finally:
        limiter.enabled = prev_enabled
        limiter._limiter.hit = prev_hit
        limiter._storage.check = prev_check
        limiter._storage_dead = False
        limiter.reset()


def test_coach_chat_rate_limited_when_redis_down(client, db, test_user, auth_headers):
    """
    Verify that /api/v1/coach/chat (20/minute) continues to enforce rate limits
    using the in-memory fallback when Redis is dead.
    """
    prev_enabled = limiter.enabled
    prev_hit = limiter._limiter.hit
    prev_check = limiter._storage.check

    limiter.enabled = True
    # Simulate Redis connection failure on primary storage
    limiter._limiter.hit = MagicMock(side_effect=Exception("Redis connection lost"))
    limiter._storage.check = MagicMock(return_value=False)
    limiter.reset()

    mock_chat_response = {
        "conversation_id": "00000000-0000-0000-0000-000000000001",
        "ai_message_id": "00000000-0000-0000-0000-000000000002",
        "message": "This is a mocked coach response.",
    }

    try:
        with patch(
            "app.routes.coach.coach_service.chat", return_value=mock_chat_response
        ):
            statuses = []
            for i in range(21):
                res = client.post(
                    "/api/v1/coach/chat",
                    json={
                        "message": f"Hello coach number {i}",
                        "turnstile_token": "test-mock-token",
                    },
                    headers=auth_headers,
                )
                statuses.append(res.status_code)

            # First 20 requests succeed (200 OK), 21st must return 429
            assert statuses[:20] == [200] * 20
            assert statuses[20] == 429
    finally:
        limiter.enabled = prev_enabled
        limiter._limiter.hit = prev_hit
        limiter._storage.check = prev_check
        limiter._storage_dead = False
        limiter.reset()
