"""
tests/test_unit_security.py
============================
Unit tests for app.core.security — JWT generation and bcrypt verification.

These tests do NOT touch the database or HTTP layer.

Coverage targets
----------------
✓ hash_password      — produces a bcrypt hash; different salts each call
✓ verify_password    — correct → True, wrong → False
✓ create_access_token  — valid JWT, type=access, sub correct, expiry correct
✓ create_refresh_token — valid JWT, type=refresh, longer expiry
✓ decode_token          — valid → claims dict; expired → JWTError; tampered → JWTError
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from freezegun import freeze_time
from jose import JWTError, jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. bcrypt — hash_password / verify_password
# ═══════════════════════════════════════════════════════════════════════════════

class TestBcrypt:

    def test_hash_password_returns_string(self):
        h = hash_password("MyPassword1!")
        assert isinstance(h, str)
        assert len(h) > 20

    def test_hash_is_not_plain_text(self):
        plain = "Secret123!"
        h = hash_password(plain)
        assert h != plain

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses a random salt — same plaintext → different hashes."""
        p = "SamePwd99!"
        h1 = hash_password(p)
        h2 = hash_password(p)
        assert h1 != h2

    def test_verify_correct_password_returns_true(self):
        plain = "CorrectHorse1!"
        h = hash_password(plain)
        assert verify_password(plain, h) is True

    def test_verify_wrong_password_returns_false(self):
        h = hash_password("RightPassword1!")
        assert verify_password("WrongPassword1!", h) is False

    def test_verify_empty_string_against_hash(self):
        h = hash_password("NonEmpty1!")
        assert verify_password("", h) is False

    def test_verify_is_case_sensitive(self):
        h = hash_password("lowercase1!")
        assert verify_password("LOWERCASE1!", h) is False


# ═══════════════════════════════════════════════════════════════════════════════
# 2. JWT — create_access_token
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateAccessToken:

    def test_returns_string(self):
        token = create_access_token("some-user-id")
        assert isinstance(token, str)

    def test_token_is_decodable(self):
        uid = str(uuid.uuid4())
        token = create_access_token(uid)
        claims = decode_token(token)
        assert claims["sub"] == uid

    def test_token_type_is_access(self):
        token = create_access_token("any-id")
        claims = decode_token(token)
        assert claims["type"] == "access"

    @freeze_time("2024-01-01 00:00:00")
    def test_access_token_expiry_matches_settings(self):
        """
        The exp claim should be now + ACCESS_TOKEN_EXPIRE_MINUTES.
        We freeze time so the assertion is deterministic.
        """
        token = create_access_token("user-123")
        claims = decode_token(token)

        expected_exp = (
            datetime(2024, 1, 1, tzinfo=timezone.utc)
            + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        actual_exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        assert actual_exp == expected_exp

    def test_uuid_subject_is_stored_as_string(self):
        uid = uuid.uuid4()
        token = create_access_token(uid)            # pass UUID object, not string
        claims = decode_token(token)
        assert claims["sub"] == str(uid)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. JWT — create_refresh_token
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateRefreshToken:

    def test_token_type_is_refresh(self):
        token = create_refresh_token("user-id")
        claims = decode_token(token)
        assert claims["type"] == "refresh"

    def test_sub_matches(self):
        uid = str(uuid.uuid4())
        token = create_refresh_token(uid)
        claims = decode_token(token)
        assert claims["sub"] == uid

    @freeze_time("2024-06-01 12:00:00")
    def test_refresh_token_expiry_is_longer_than_access(self):
        """Refresh tokens must outlive access tokens by a wide margin."""
        access  = create_access_token("u")
        refresh = create_refresh_token("u")

        access_exp  = decode_token(access)["exp"]
        refresh_exp = decode_token(refresh)["exp"]

        assert refresh_exp > access_exp

    @freeze_time("2024-06-01 12:00:00")
    def test_refresh_token_expiry_matches_settings(self):
        uid = str(uuid.uuid4())
        token = create_refresh_token(uid)
        claims = decode_token(token)

        expected_exp = (
            datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        actual_exp = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
        assert actual_exp == expected_exp


# ═══════════════════════════════════════════════════════════════════════════════
# 4. decode_token
# ═══════════════════════════════════════════════════════════════════════════════

class TestDecodeToken:

    def test_valid_token_returns_claims_dict(self):
        uid = "test-uid-abc"
        token = create_access_token(uid)
        claims = decode_token(token)

        assert isinstance(claims, dict)
        assert "sub" in claims
        assert "exp" in claims
        assert "type" in claims

    def test_expired_token_raises_jwterror(self):
        """A token expired 1 second ago must raise JWTError."""
        expired = jwt.encode(
            {
                "sub": "user-id",
                "type": "access",
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        with pytest.raises(JWTError):
            decode_token(expired)

    def test_tampered_payload_raises_jwterror(self):
        """Altering any part of the token must invalidate the signature."""
        token = create_access_token("legit-user")
        header, payload, sig = token.split(".")
        import base64
        import json
        decoded = base64.urlsafe_b64decode(payload + "==")
        data = json.loads(decoded)
        data["sub"] = "tampered-user"
        tampered_payload = base64.urlsafe_b64encode(json.dumps(data).encode()).decode().replace("=", "")
        tampered = f"{header}.{tampered_payload}.{sig}"

        with pytest.raises(JWTError):
            decode_token(tampered)

    def test_wrong_secret_raises_jwterror(self):
        """A token signed with a different secret must be rejected."""
        bad_token = jwt.encode(
            {"sub": "x", "type": "access"},
            "wrong-secret-key",
            algorithm=settings.ALGORITHM,
        )
        with pytest.raises(JWTError):
            decode_token(bad_token)

    def test_garbage_string_raises_jwterror(self):
        with pytest.raises(JWTError):
            decode_token("not.a.token")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. FastAPI Dependencies — get_db, get_current_user, get_current_active_user
# ═══════════════════════════════════════════════════════════════════════════════

class TestFastAPIDependencies:

    def test_get_db_yields_session(self):
        from app.core.security import get_db
        from sqlalchemy.orm import Session
        db_generator = get_db()
        db_session = next(db_generator)
        assert isinstance(db_session, Session)
        try:
            next(db_generator)
        except StopIteration:
            pass

    def test_get_db_rolls_back_on_exception(self):
        from app.core.security import get_db
        db_generator = get_db()
        next(db_generator)
        with pytest.raises(Exception):
            db_generator.throw(Exception("Simulated DB error"))

    def test_get_current_user_no_sub_raises_401(self, db):
        from app.core.security import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException
        token = jwt.encode(
            {"type": "access", "exp": datetime.now(timezone.utc) + timedelta(minutes=30)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(creds, db)
        assert exc_info.value.status_code == 401

    def test_get_current_user_nonexistent_user_raises_401(self, db):
        from app.core.security import get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from fastapi import HTTPException
        token = create_access_token(subject=str(uuid.uuid4()))
        creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(creds, db)
        assert exc_info.value.status_code == 401

    def test_get_current_active_user_soft_deleted_raises_403(self, make_user):
        from app.core.security import get_current_active_user
        from fastapi import HTTPException
        user = make_user(deleted=True)
        with pytest.raises(HTTPException) as exc_info:
            get_current_active_user(current_user=user)
        assert exc_info.value.status_code == 403

    def test_get_current_active_user_happy_path(self, make_user):
        from app.core.security import get_current_active_user
        user = make_user()
        active_user = get_current_active_user(current_user=user)
        assert active_user == user
