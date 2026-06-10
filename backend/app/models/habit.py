"""
Habit ORM model.

Table: habits
- UUID PK
- Tracks daily sustainability habit completions per user
- habit_type ENUM
- Indexes: user_id, activity_date (both from schema doc)
"""
import uuid
from datetime import date

from sqlalchemy import Boolean, Date, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin
from app.models.enums import HabitType


class Habit(Base, CreatedAtMixin):
    __tablename__ = "habits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Habit details
    habit_type: Mapped[HabitType] = mapped_column(String(30), nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    carbon_saved: Mapped[float | None] = mapped_column(Float, nullable=True)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="habits")

    __table_args__ = (
        Index("ix_habits_user_id", "user_id"),           # schema doc requirement
        Index("ix_habits_activity_date", "activity_date"), # schema doc requirement
        Index("ix_habits_user_date", "user_id", "activity_date"),  # composite for streak queries
        Index("ix_habits_habit_type", "habit_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<Habit id={self.id} user_id={self.user_id} "
            f"type={self.habit_type!r} date={self.activity_date}>"
        )
