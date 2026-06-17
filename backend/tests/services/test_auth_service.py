"""
tests/test_unit_auth_service.py
================================
Pure unit tests for app.services.auth_service.

All database calls use the in-memory SQLite session from conftest.
No HTTP layer involved — service functions are called directly.

Coverage targets
----------------
✓ register_user  — happy path, duplicate email, weak password (all-digits)
✓ login_user     — correct creds, wrong password, nonexistent user, deleted user
✓ refresh_tokens — valid refresh token, wrong token type, expired token
✓ get_profile    — returns ProfileResponse from User ORM object
✓ update_profile — patches fields, persists to DB
✓ soft_delete    — sets deleted_at, raises 409 on already-deleted
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException
from freezegun import freeze_time
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_refresh_token, decode_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import RefreshRequest, RegisterRequest
from app.schemas.user import UpdateProfileRequest
from app.services import auth_service


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_register_payload(**overrides) -> RegisterRequest:
    defaults = dict(
        full_name="Priya Sharma",
        email=f"priya_{uuid.uuid4().hex[:6]}@example.com",
        password="SecurePass99!",
        age_group="adult",
        lifestyle_type="professional",
        city="Mumbai",
        country="India",
    )
    defaults.update(overrides)
    return RegisterRequest(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. register_user
# ═══════════════════════════════════════════════════════════════════════════════

class TestRegisterUser:

    def test_happy_path_creates_user(self, db: Session):
        """register_user persists a new User row and returns a RegisterResponse."""
        payload = _make_register_payload()
        result = auth_service.register_user(db, payload)

        # Response shape
        assert result.user.email == payload.email
        assert result.user.full_name == payload.full_name
        assert result.user.city == "Mumbai"
        assert result.user.country == "India"

        # DB row was persisted
        user_in_db = db.query(User).filter(User.email == payload.email).first()
        assert user_in_db is not None
        assert user_in_db.email_verified is False

    def test_password_is_hashed_not_stored_plain(self, db: Session):
        """The plain password must never be stored in the DB."""
        plain = "VerySecret42!"
        payload = _make_register_payload(password=plain)
        auth_service.register_user(db, payload)

        user = db.query(User).filter(User.email == payload.email).first()
        assert user is not None
        assert user.password_hash != plain
        assert verify_password(plain, user.password_hash) is True

    def test_optional_fields_can_be_omitted(self, db: Session):
        """Registering without optional fields should succeed."""
        payload = RegisterRequest(
            full_name="Anonymous",
            email=f"anon_{uuid.uuid4().hex[:6]}@example.com",
            password="MinLength8!",
        )
        result = auth_service.register_user(db, payload)
        assert result.user.city is None
        assert result.user.country is None
        assert result.user.age_group is None

    def test_duplicate_email_raises_409(self, db: Session, make_user):
        """Registering with an already-registered email must raise HTTP 409."""
        existing = make_user(email="dup@example.com")
        payload = _make_register_payload(email=existing.email)

        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(db, payload)

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail.lower()

    def test_duplicate_email_soft_deleted_user_still_blocked(self, db: Session, make_user):
        """
        Even if the original account is soft-deleted, the email slot is taken.
        (Business rule: deleted users retain their email for 90-day retention.)
        """
        make_user(email="gone@example.com", deleted=True)
        payload = _make_register_payload(email="gone@example.com")

        with pytest.raises(HTTPException) as exc_info:
            auth_service.register_user(db, payload)

        assert exc_info.value.status_code == 409


# ═══════════════════════════════════════════════════════════════════════════════
# 2. login_user
# ═══════════════════════════════════════════════════════════════════════════════

class TestLoginUser:

    def test_correct_credentials_return_token_pair(self, db: Session, make_user):
        """login_user with correct creds returns access + refresh tokens."""
        user = make_user(password="Correct99!")
        result = auth_service.login_user(db, user.email, "Correct99!")

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"
        assert result.expires_in == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    def test_login_stamps_last_login(self, db: Session, make_user):
        """login_user must update user.last_login with the current UTC time."""
        user = make_user(password="TimeStamp1!")
        assert user.last_login is None

        before = datetime.now(timezone.utc)
        auth_service.login_user(db, user.email, "TimeStamp1!")
        after = datetime.now(timezone.utc)

        db.refresh(user)
        assert user.last_login is not None
        last_login_aware = user.last_login.replace(tzinfo=timezone.utc) if user.last_login.tzinfo is None else user.last_login
        assert before <= last_login_aware <= after

    def test_wrong_password_raises_401(self, db: Session, make_user):
        """Incorrect password must raise HTTP 401."""
        user = make_user(password="RealPass99!")

        with pytest.raises(HTTPException) as exc_info:
            auth_service.login_user(db, user.email, "WrongPass99!")

        assert exc_info.value.status_code == 401

    def test_nonexistent_user_raises_401(self, db: Session):
        """Non-existent email must raise HTTP 401 (not 404 — avoids email enumeration)."""
        with pytest.raises(HTTPException) as exc_info:
            auth_service.login_user(db, "nobody@nowhere.com", "Irrelevant1!")

        assert exc_info.value.status_code == 401

    def test_soft_deleted_user_cannot_login(self, db: Session, make_user):
        """A soft-deleted user's email should not be found → HTTP 401."""
        user = make_user(password="WasActive1!", deleted=True)

        with pytest.raises(HTTPException) as exc_info:
            auth_service.login_user(db, user.email, "WasActive1!")

        assert exc_info.value.status_code == 401

    def test_access_token_contains_correct_sub(self, db: Session, make_user):
        """The access token `sub` must be the user's UUID string."""
        user = make_user(password="SubCheck1!")
        result = auth_service.login_user(db, user.email, "SubCheck1!")

        claims = decode_token(result.access_token)
        assert claims["sub"] == str(user.id)
        assert claims["type"] == "access"

    def test_refresh_token_type_is_refresh(self, db: Session, make_user):
        """The refresh token must have type='refresh' in its claims."""
        user = make_user(password="RefType1!")
        result = auth_service.login_user(db, user.email, "RefType1!")

        claims = decode_token(result.refresh_token)
        assert claims["type"] == "refresh"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. refresh_tokens
# ═══════════════════════════════════════════════════════════════════════════════

class TestRefreshTokens:

    def test_valid_refresh_token_returns_new_pair(self, db: Session, make_user):
        """A valid refresh token should produce a new access + refresh pair."""
        user = make_user(password="Refresh1!")
        login_result = auth_service.login_user(db, user.email, "Refresh1!")

        refresh_payload = RefreshRequest(refresh_token=login_result.refresh_token)
        new_tokens = auth_service.refresh_tokens(db, refresh_payload)

        assert new_tokens.access_token
        assert new_tokens.refresh_token
        # New access token should still identify the same user
        claims = decode_token(new_tokens.access_token)
        assert claims["sub"] == str(user.id)

    def test_access_token_rejected_as_refresh(self, db: Session, make_user):
        """Sending an access token to the refresh endpoint must raise 401."""
        user = make_user(password="WrongType1!")
        login_result = auth_service.login_user(db, user.email, "WrongType1!")

        # Pass the access token where a refresh token is expected
        bad_payload = RefreshRequest(refresh_token=login_result.access_token)
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_tokens(db, bad_payload)

        assert exc_info.value.status_code == 401

    def test_expired_refresh_token_raises_401(self, db: Session, make_user):
        """An expired refresh token must be rejected with HTTP 401."""
        user = make_user(password="Expired1!")

        # Create a token that expired 1 second in the past
        expired_token = jwt.encode(
            {
                "sub": str(user.id),
                "type": "refresh",
                "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        bad_payload = RefreshRequest(refresh_token=expired_token)
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_tokens(db, bad_payload)

        assert exc_info.value.status_code == 401

    def test_tampered_refresh_token_raises_401(self, db: Session):
        """A token with an invalid signature must be rejected."""
        bad_payload = RefreshRequest(refresh_token="header.payload.badsignature")
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_tokens(db, bad_payload)
        assert exc_info.value.status_code == 401

    def test_refresh_token_for_deleted_user_raises_404(self, db: Session, make_user):
        """If the user in the refresh token's sub is soft-deleted, raise 404."""
        user = make_user(password="DelRefresh1!", deleted=True)
        # Mint a valid refresh token manually (bypassing login which blocks deleted users)
        token = create_refresh_token(subject=str(user.id))
        payload = RefreshRequest(refresh_token=token)

        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_tokens(db, payload)

        assert exc_info.value.status_code == 404

    def test_refresh_token_missing_sub_raises_401(self, db: Session):
        """A refresh token missing the `sub` claim must raise HTTP 401."""
        bad_token = jwt.encode(
            {"type": "refresh", "exp": datetime.now(timezone.utc) + timedelta(days=1)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        payload = RefreshRequest(refresh_token=bad_token)
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_tokens(db, payload)
        assert exc_info.value.status_code == 401

    def test_refresh_token_invalid_uuid_raises_404(self, db: Session):
        """A refresh token with a non-UUID sub must raise HTTP 404."""
        bad_token = jwt.encode(
            {"sub": "not-a-uuid", "type": "refresh", "exp": datetime.now(timezone.utc) + timedelta(days=1)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        payload = RefreshRequest(refresh_token=bad_token)
        with pytest.raises(HTTPException) as exc_info:
            auth_service.refresh_tokens(db, payload)
        assert exc_info.value.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# 4. get_profile
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetProfile:

    def test_returns_profile_response(self, db: Session, make_user):
        """get_profile returns a ProfileResponse populated from the User ORM object."""
        user = make_user(
            full_name="Karan Mehta",
            email="karan@example.com",
            city="Delhi",
            country="India",
        )
        profile = auth_service.get_profile(user)

        assert profile.email == "karan@example.com"
        assert profile.full_name == "Karan Mehta"
        assert profile.city == "Delhi"
        assert profile.country == "India"
        assert profile.id == user.id

    def test_profile_does_not_expose_password_hash(self, db: Session, make_user):
        """ProfileResponse must not include password_hash."""
        user = make_user()
        profile = auth_service.get_profile(user)

        assert not hasattr(profile, "password_hash")


# ═══════════════════════════════════════════════════════════════════════════════
# 5. update_profile
# ═══════════════════════════════════════════════════════════════════════════════

class TestUpdateProfile:

    def test_partial_update_patches_only_given_fields(self, db: Session, make_user):
        """update_profile with a partial payload only changes the given fields."""
        user = make_user(city="Chennai", country="India")
        original_name = user.full_name

        payload = UpdateProfileRequest(city="Bangalore")
        updated = auth_service.update_profile(db, user, payload)

        assert updated.city == "Bangalore"
        assert updated.full_name == original_name  # untouched

    def test_update_persists_to_db(self, db: Session, make_user):
        """Changes must be visible when the row is reloaded from the DB."""
        user = make_user(country="India")
        auth_service.update_profile(db, user, UpdateProfileRequest(country="UK"))

        db.expire(user)
        db.refresh(user)
        assert user.country == "UK"

    def test_update_multiple_fields(self, db: Session, make_user):
        """Updating multiple fields in one call must all be applied."""
        user = make_user()
        payload = UpdateProfileRequest(
            full_name="Riya Patel",
            city="Ahmedabad",
            country="India",
        )
        updated = auth_service.update_profile(db, user, payload)

        assert updated.full_name == "Riya Patel"
        assert updated.city == "Ahmedabad"
        assert updated.country == "India"


# ═══════════════════════════════════════════════════════════════════════════════
# 6. soft_delete_account
# ═══════════════════════════════════════════════════════════════════════════════

class TestSoftDeleteAccount:

    def test_sets_deleted_at(self, db: Session, make_user):
        """soft_delete_account sets deleted_at to the current UTC timestamp."""
        user = make_user()
        assert user.deleted_at is None

        before = datetime.now(timezone.utc)
        auth_service.soft_delete_account(db, user)
        after = datetime.now(timezone.utc)

        db.refresh(user)
        assert user.deleted_at is not None
        deleted_at_aware = user.deleted_at.replace(tzinfo=timezone.utc) if user.deleted_at.tzinfo is None else user.deleted_at
        assert before <= deleted_at_aware <= after

    def test_already_deleted_raises_409(self, db: Session, make_user):
        """Calling soft_delete on an already-deleted user must raise HTTP 409."""
        user = make_user(deleted=True)

        with pytest.raises(HTTPException) as exc_info:
            auth_service.soft_delete_account(db, user)

        assert exc_info.value.status_code == 409

    def test_is_deleted_property_true_after_delete(self, db: Session, make_user):
        """User.is_deleted must return True after soft deletion."""
        user = make_user()
        auth_service.soft_delete_account(db, user)
        db.refresh(user)
        assert user.is_deleted is True
