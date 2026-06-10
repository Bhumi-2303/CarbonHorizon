"""
Goal ORM model.

Table: goals
- UUID PK
- Sustainability objectives per user
- status ENUM (active, completed, expired)
- Index: user_id
"""
import uuid
from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import GoalStatus


class Goal(Base, TimestampMixin):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Goal definition
    goal_name: Mapped[str] = mapped_column(String(255), nullable=False)
    goal_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Targets
    target_reduction_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_emission_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # State
    status: Mapped[GoalStatus] = mapped_column(
        String(15), nullable=False, default=GoalStatus.active
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="goals")

    __table_args__ = (
        Index("ix_goals_user_id", "user_id"),
        Index("ix_goals_status", "status"),
        Index("ix_goals_target_date", "target_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<Goal id={self.id} user_id={self.user_id} "
            f"name={self.goal_name!r} status={self.status!r}>"
        )
