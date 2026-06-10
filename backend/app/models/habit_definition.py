"""
HabitDefinition ORM model.

Table: habit_definitions
- UUID PK
- Reference / lookup table for habit → carbon saving factor
- e.g. public_transport → 1.2 kg CO₂e per trip
"""
import uuid

from sqlalchemy import Float, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import TimestampMixin


class HabitDefinition(Base, TimestampMixin):
    __tablename__ = "habit_definitions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    # Identifies which habit type this definition covers
    habit_type: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )

    # Conversion factor
    carbon_saving_factor: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "kg CO₂e per trip"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_habit_definitions_habit_type", "habit_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<HabitDefinition id={self.id} habit_type={self.habit_type!r} "
            f"factor={self.carbon_saving_factor}>"
        )
