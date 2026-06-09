"""
AuthService — authentication business logic.
No logic implemented yet; method stubs only.
"""
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.token import Token


class AuthService:

    @staticmethod
    def authenticate(db: Session, email: str, password: str) -> User | None:
        """Verify credentials and return User or None."""
        raise NotImplementedError

    @staticmethod
    def create_tokens(user: User) -> Token:
        """Issue access + refresh token pair for a user."""
        raise NotImplementedError

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Token:
        """Validate refresh token and return a new token pair."""
        raise NotImplementedError
