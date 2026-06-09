"""
UserService — business logic for user management.
No logic implemented yet; method stubs only.
"""
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        """Fetch a user by primary key."""
        raise NotImplementedError

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        """Fetch a user by email address."""
        raise NotImplementedError

    @staticmethod
    def list_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
        """Return a paginated list of users."""
        raise NotImplementedError

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    @staticmethod
    def create(db: Session, payload: UserCreate) -> User:
        """Create a new user (hashes password before saving)."""
        raise NotImplementedError

    @staticmethod
    def update(db: Session, user: User, payload: UserUpdate) -> User:
        """Apply partial updates to an existing user."""
        raise NotImplementedError

    @staticmethod
    def delete(db: Session, user: User) -> None:
        """Hard-delete a user record."""
        raise NotImplementedError
