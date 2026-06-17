"""
User ORM model.

Table: users
- UUID PK
- Full profile + auth fields
- age_group / lifestyle_type ENUMs
- Soft delete via deleted_at
- Index: email (UNIQUE), deleted_at
"""
import uuid

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, SoftDeleteMixin
from app.models.enums import AgeGroup, LifestyleType


class User(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    # Primary key
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # Identity
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    # Profile
    age_group: Mapped[AgeGroup | None] = mapped_column(
        String(20), nullable=True
    )
    lifestyle_type: Mapped[LifestyleType | None] = mapped_column(
        String(20), nullable=True
    )
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Auth state
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    preferences: Mapped["UserPreferences"] = relationship(
        "UserPreferences", back_populates="user", uselist=False, cascade="all, delete-orphan", lazy="joined"
    )
    carbon_assessments: Mapped[list["CarbonAssessment"]] = relationship(
        "CarbonAssessment", back_populates="user", cascade="all, delete-orphan"
    )
    goals: Mapped[list["Goal"]] = relationship(
        "Goal", back_populates="user", cascade="all, delete-orphan"
    )
    simulations: Mapped[list["Simulation"]] = relationship(
        "Simulation", back_populates="user", cascade="all, delete-orphan"
    )
    forecasts: Mapped[list["Forecast"]] = relationship(
        "Forecast", back_populates="user", cascade="all, delete-orphan"
    )
    habits: Mapped[list["Habit"]] = relationship(
        "Habit", back_populates="user", cascade="all, delete-orphan"
    )
    ai_conversations: Mapped[list["AIConversation"]] = relationship(
        "AIConversation", back_populates="user", cascade="all, delete-orphan"
    )

    # Table-level indexes (email index declared inline above; extra below)
    __table_args__ = (
        Index("ix_users_country", "country"),       # geographic queries
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r}>"
