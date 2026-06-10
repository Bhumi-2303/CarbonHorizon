"""
UserPreferences ORM model.

Table: user_preferences
- UUID PK
- 1-to-1 with users
- theme / measurement_unit ENUMs
"""
import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import Theme, MeasurementUnit


class UserPreferences(Base, TimestampMixin):
    __tablename__ = "user_preferences"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,   # enforces 1-to-1
    )

    theme: Mapped[Theme] = mapped_column(
        String(10), nullable=False, default=Theme.system
    )
    language: Mapped[str] = mapped_column(
        String(20), nullable=False, default="en"
    )
    notifications_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    measurement_unit: Mapped[MeasurementUnit] = mapped_column(
        String(10), nullable=False, default=MeasurementUnit.metric
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="preferences")

    __table_args__ = (
        Index("ix_user_preferences_user_id", "user_id"),
    )

    def __repr__(self) -> str:
        return f"<UserPreferences user_id={self.user_id} theme={self.theme!r}>"
