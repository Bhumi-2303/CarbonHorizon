"""
EmissionInputs ORM model.

Table: emission_inputs
- UUID PK
- 1-to-1 with carbon_assessments (raw survey data)
- transport_mode / diet_type ENUMs
"""
import uuid

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin
from app.models.enums import TransportMode, DietType


class EmissionInputs(Base, CreatedAtMixin):
    __tablename__ = "emission_inputs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("carbon_assessments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # 1-to-1 with assessment
    )

    # Transport
    transport_mode: Mapped[TransportMode | None] = mapped_column(
        String(15), nullable=True
    )
    distance_km: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Energy
    electricity_kwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    ac_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    lpg_usage: Mapped[float | None] = mapped_column(Float, nullable=True)
    solar_usage: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

    # Food & Waste
    diet_type: Mapped[DietType | None] = mapped_column(String(20), nullable=True)
    recycling_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    plastic_usage_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Household
    household_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationship
    assessment: Mapped["CarbonAssessment"] = relationship(
        "CarbonAssessment", back_populates="emission_inputs"
    )

    __table_args__ = (
        Index("ix_emission_inputs_assessment_id", "assessment_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<EmissionInputs id={self.id} assessment_id={self.assessment_id} "
            f"transport={self.transport_mode!r}>"
        )
