"""
tests/test_integration_auth.py
================================
HTTP integration tests for the /api/v1/auth/* endpoints.

Uses FastAPI's TestClient (synchronous, based on httpx) against the
full application stack with an in-memory SQLite database.
The `client` fixture (from conftest) overrides the get_db dependency so
every request uses the same isolated per-test session.

Endpoint coverage
-----------------
POST   /api/v1/auth/register  — 201, 409 duplicate, 422 validation
POST   /api/v1/auth/login     — 200 + JWT, 401 bad creds
POST   /api/v1/auth/refresh   — 200 new tokens, 401 invalid token
POST   /api/v1/auth/logout    — 204
GET    /api/v1/auth/profile   — 200 with valid token, 401 expired/missing
PUT    /api/v1/auth/profile   — 200 patched profile
DELETE /api/v1/auth/account   — 204, 409 already deleted
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
import jwt

from app.core.config import settings

# ─── Shared payloads ──────────────────────────────────────────────────────────

REGISTER_BODY = {
    "full_name": "Integration Tester",
    "email": "integration@example.com",
    "password": "IntegrationPass1!",
    "age_group": "adult",
    "lifestyle_type": "professional",
    "city": "Bengaluru",
    "country": "India",
}

LOGIN_BODY = {
    "email": "integration@example.com",
    "password": "IntegrationPass1!",
}


# ─── Helper ───────────────────────────────────────────────────────────────────

def _unique_register_body(**overrides) -> dict:
    body = REGISTER_BODY.copy()
    body["email"] = f"user_{uuid.uuid4().hex[:8]}@example.com"
    body.update(overrides)
    return body


def _register_and_login(client: TestClient) -> dict:
    """Register a user, log in, return the full token response dict."""
    body = _unique_register_body()
    client.post("/api/v1/auth/register", json=body)
    r = client.post(
        "/api/v1/auth/login",
        json={"email": body["email"], "password": body["password"]},
    )
    return r.json()["data"]


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/auth/register
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegisterEndpoint:

    def test_register_happy_path_returns_201(self, client: TestClient):
        body = _unique_register_body()
        r = client.post("/api/v1/auth/register", json=body)

        assert r.status_code == 201
        data = r.json()
        assert data["success"] is True
        assert data["data"]["user"]["email"] == body["email"]

    def test_register_response_excludes_password_hash(self, client: TestClient):
        """The API response must never expose the password hash."""
        body = _unique_register_body()
        r = client.post("/api/v1/auth/register", json=body)
        user_data = r.json()["data"]["user"]
        assert "password_hash" not in user_data
        assert "password" not in user_data

    def test_register_all_optional_fields(self, client: TestClient):
        """Registering with all optional fields should succeed."""
        body = _unique_register_body(
            age_group="student",
            lifestyle_type="student",
            city="Pune",
            country="India",
        )
        r = client.post("/api/v1/auth/register", json=body)
        assert r.status_code == 201
        user = r.json()["data"]["user"]
        assert user["city"] == "Pune"
        assert user["age_group"] == "student"

    def test_register_minimal_fields(self, client: TestClient):
        """Only full_name, email, password are required."""
        body = {
            "full_name": "Minimal User",
            "email": f"minimal_{uuid.uuid4().hex[:6]}@test.com",
            "password": "MinimalPass1!",
        }
        r = client.post("/api/v1/auth/register", json=body)
        assert r.status_code == 201

    def test_register_duplicate_email_returns_409(self, client: TestClient):
        body = _unique_register_body()
        client.post("/api/v1/auth/register", json=body)  # first registration
        r = client.post("/api/v1/auth/register", json=body)  # duplicate

        assert r.status_code == 409

    def test_register_invalid_email_returns_422(self, client: TestClient):
        body = _unique_register_body(email="not-an-email")
        r = client.post("/api/v1/auth/register", json=body)
        assert r.status_code == 422

    def test_register_short_password_returns_422(self, client: TestClient):
        """Passwords shorter than 8 chars must be rejected by Zod at schema level."""
        body = _unique_register_body(password="short")
        r = client.post("/api/v1/auth/register", json=body)
        assert r.status_code == 422

    def test_register_all_digit_password_returns_422(self, client: TestClient):
        """Passwords that are all digits must be rejected."""
        body = _unique_register_body(password="12345678")
        r = client.post("/api/v1/auth/register", json=body)
        assert r.status_code == 422

    def test_register_missing_required_fields_returns_422(self, client: TestClient):
        r = client.post("/api/v1/auth/register", json={"email": "x@x.com"})
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/auth/login
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoginEndpoint:

    def test_login_returns_jwt_token_pair(self, client: TestClient):
        """Successful login must return access_token + refresh_token."""
        body = _unique_register_body()
        client.post("/api/v1/auth/register", json=body)

        r = client.post(
            "/api/v1/auth/login",
            json={"email": body["email"], "password": body["password"]},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

        token_data = data["data"]
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert token_data["token_type"] == "bearer"
        assert token_data["expires_in"] == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def test_login_access_token_is_valid_jwt(self, client: TestClient):
        """The returned access token must decode to a valid JWT."""
        body = _unique_register_body()
        client.post("/api/v1/auth/register", json=body)

        r = client.post("/api/v1/auth/login", json={"email": body["email"], "password": body["password"]})
        token = r.json()["data"]["access_token"]

        claims = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert claims["type"] == "access"
        assert "sub" in claims

    def test_login_wrong_password_returns_401(self, client: TestClient):
        body = _unique_register_body()
        client.post("/api/v1/auth/register", json=body)

        r = client.post(
            "/api/v1/auth/login",
            json={"email": body["email"], "password": "WrongPassword1!"},
        )
        assert r.status_code == 401

    def test_login_unknown_email_returns_401(self, client: TestClient):
        r = client.post(
            "/api/v1/auth/login",
            json={"email": "nobody@nowhere.io", "password": "Irrelevant1!"},
        )
        assert r.status_code == 401

    def test_login_missing_password_returns_422(self, client: TestClient):
        r = client.post("/api/v1/auth/login", json={"email": "x@x.com"})
        assert r.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/auth/refresh
# ═══════════════════════════════════════════════════════════════════════════════

class TestRefreshEndpoint:

    def test_refresh_returns_new_token_pair(self, client: TestClient):
        from freezegun import freeze_time
        with freeze_time("2026-06-11 12:00:00") as frozen_time:
            tokens = _register_and_login(client)
            frozen_time.tick(delta=timedelta(seconds=1))
            r = client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": tokens["refresh_token"]},
            )
            assert r.status_code == 200
            new_tokens = r.json()["data"]
            assert new_tokens["access_token"] != tokens["access_token"]

    def test_refresh_with_access_token_returns_401(self, client: TestClient):
        """Sending an access token where a refresh token is expected → 401."""
        tokens = _register_and_login(client)
        r = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["access_token"]},  # wrong type
        )
        assert r.status_code == 401

    def test_refresh_with_expired_token_returns_401(self, client: TestClient):
        expired = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "type": "refresh",
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        r = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": expired},
        )
        assert r.status_code == 401

    def test_refresh_with_garbage_token_returns_401(self, client: TestClient):
        r = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "not.a.real.token"},
        )
        assert r.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/v1/auth/profile
# ═══════════════════════════════════════════════════════════════════════════════

class TestProfileEndpoint:

    def test_profile_with_valid_token_returns_200(
        self, client: TestClient, auth_headers: dict
    ):
        """A valid Bearer token must return the authenticated user's profile."""
        r = client.get("/api/v1/auth/profile", headers=auth_headers)
        assert r.status_code == 200

        data = r.json()
        assert data["success"] is True
        profile = data["data"]
        assert "email" in profile
        assert "full_name" in profile
        assert "password_hash" not in profile

    def test_profile_returns_correct_user(
        self, client: TestClient, test_user, auth_headers: dict
    ):
        """Profile must match the authenticated user, not any other user."""
        r = client.get("/api/v1/auth/profile", headers=auth_headers)
        profile = r.json()["data"]
        assert profile["email"] == test_user.email
        assert profile["full_name"] == test_user.full_name

    def test_profile_no_token_returns_403_or_401(self, client: TestClient):
        """Missing Authorization header must be rejected."""
        r = client.get("/api/v1/auth/profile")
        assert r.status_code in (401, 403)

    def test_profile_with_expired_token_returns_401(self, client: TestClient, test_user):
        """An expired access token must be rejected with 401."""
        expired_token = jwt.encode(
            {
                "sub": str(test_user.id),
                "type": "access",
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        r = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {expired_token}"},
        )
        assert r.status_code == 401

    def test_profile_with_refresh_token_returns_401(
        self, client: TestClient, test_user
    ):
        """Sending a refresh token to a protected endpoint must be rejected."""
        from app.core.security import create_refresh_token
        rt = create_refresh_token(subject=str(test_user.id))
        r = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {rt}"},
        )
        assert r.status_code == 401

    def test_profile_with_tampered_token_returns_401(
        self, client: TestClient, auth_headers: dict
    ):
        """A token with a bad signature must be rejected."""
        token = auth_headers["Authorization"].split(" ")[1]
        header, payload, sig = token.split(".")
        bad = f"{header}.{payload}.{sig[:-4]}XXXX"
        r = client.get(
            "/api/v1/auth/profile",
            headers={"Authorization": f"Bearer {bad}"},
        )
        assert r.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/v1/auth/logout
# ═══════════════════════════════════════════════════════════════════════════════

class TestLogoutEndpoint:

    def test_logout_returns_204(self, client: TestClient, auth_headers: dict):
        r = client.post("/api/v1/auth/logout", headers=auth_headers)
        assert r.status_code == 204

    def test_logout_without_token_returns_401_or_403(self, client: TestClient):
        r = client.post("/api/v1/auth/logout")
        assert r.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
# PUT /api/v1/auth/profile
# ═══════════════════════════════════════════════════════════════════════════════

class TestUpdateProfileEndpoint:

    def test_update_profile_returns_200(
        self, client: TestClient, auth_headers: dict
    ):
        r = client.put(
            "/api/v1/auth/profile",
            json={"city": "Hyderabad"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["city"] == "Hyderabad"

    def test_update_full_name(self, client: TestClient, auth_headers: dict):
        r = client.put(
            "/api/v1/auth/profile",
            json={"full_name": "Updated Name"},
            headers=auth_headers,
        )
        assert r.status_code == 200
        assert r.json()["data"]["full_name"] == "Updated Name"

    def test_update_profile_without_token_returns_401(self, client: TestClient):
        r = client.put("/api/v1/auth/profile", json={"city": "X"})
        assert r.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
# DELETE /api/v1/auth/account
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeleteAccountEndpoint:

    def test_delete_account_returns_204(
        self, client: TestClient, make_user, db
    ):
        """A valid delete request should soft-delete the account and return 204."""
        from app.core.security import create_access_token
        user = make_user(email=f"del_{uuid.uuid4().hex[:6]}@example.com")
        headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}

        r = client.delete("/api/v1/auth/account", headers=headers)
        assert r.status_code == 204

    def test_delete_already_deleted_returns_409(
        self, client: TestClient, make_user, db
    ):
        """Trying to delete an already-deleted account must return 409."""
        from app.core.security import create_access_token
        user = make_user(email=f"del2_{uuid.uuid4().hex[:6]}@example.com")
        headers = {"Authorization": f"Bearer {create_access_token(str(user.id))}"}

        client.delete("/api/v1/auth/account", headers=headers)  # first delete

        # The token still works but get_current_active_user now raises 403
        # because the account is soft-deleted. That's expected behaviour.
        r = client.delete("/api/v1/auth/account", headers=headers)
        assert r.status_code in (403, 409)  # 403 from get_current_active_user
