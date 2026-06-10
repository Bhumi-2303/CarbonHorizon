"""
Simulation ORM model.

Table: simulations
- UUID PK
- What-if scenario modelling
- simulation_data stored as JSONB (PostgreSQL) / JSON (SQLite)
- Index: user_id
"""
import uuid
from typing import Any

from sqlalchemy import Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin


class Simulation(Base, TimestampMixin):
    __tablename__ = "simulations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Scenario metadata
    scenario_name: Mapped[str] = mapped_column(String(255), nullable=False)
    scenario_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Emission values (kg CO₂e)
    current_emission: Mapped[float | None] = mapped_column(Float, nullable=True)
    projected_emission: Mapped[float | None] = mapped_column(Float, nullable=True)
    reduction_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    estimated_carbon_saved: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Flexible scenario payload (transport choices, energy mix, etc.)
    simulation_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="simulations")

    __table_args__ = (
        Index("ix_simulations_user_id", "user_id"),
        Index("ix_simulations_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Simulation id={self.id} user_id={self.user_id} "
            f"scenario={self.scenario_name!r}>"
        )
