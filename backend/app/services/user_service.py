"""
UserService — business logic for user management.
No logic implemented yet; method stubs only.
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import hash_password


class UserService:
    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
        """Fetch a user by primary key."""
        return db.get(User, user_id)

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        """Fetch a user by email address."""
        stmt = select(User).where(User.email == email)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        """Return a paginated list of users."""
        stmt = select(User).offset(skip).limit(limit)
        return list(db.execute(stmt).scalars().all())

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def create(db: Session, payload: UserCreate) -> User:
        """Create a new user (hashes password before saving)."""
        terms_acc = getattr(payload, "terms_accepted", False)
        terms_ver = getattr(payload, "terms_version", None)
        db_user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name,
            age=payload.age,
            gender=payload.gender,
            country=payload.country,
            state_province=payload.state_province,
            city=payload.city,
            age_group=payload.age_group,
            lifestyle_type=payload.lifestyle_type,
            terms_accepted=terms_acc,
            terms_version=terms_ver,
            terms_accepted_at=datetime.now(timezone.utc) if terms_acc else None,
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user

    @staticmethod
    def update(db: Session, user: User, payload: UserUpdate) -> User:
        """Apply partial updates to an existing user."""
        update_data = payload.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete(db: Session, user: User) -> None:
        """Hard-delete a user record."""
        db.delete(user)
        db.commit()
