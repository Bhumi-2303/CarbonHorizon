"""
CarbonAssessment ORM model.

Table: carbon_assessments
- UUID PK
- Stores calculated emission totals per category
- assessment_period ENUM
- Index: user_id
"""
import uuid

from sqlalchemy import Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import AssessmentPeriod


class CarbonAssessment(Base, TimestampMixin):
    __tablename__ = "carbon_assessments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Emission breakdown (kg CO₂e)
    transport_emission: Mapped[float | None] = mapped_column(Float, nullable=True)
    energy_emission: Mapped[float | None] = mapped_column(Float, nullable=True)
    food_emission: Mapped[float | None] = mapped_column(Float, nullable=True)
    waste_emission: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_emission: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Score and versioning
    carbon_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    calculation_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    factor_version: Mapped[str | None] = mapped_column(String(20), nullable=True)

    # Period
    assessment_period: Mapped[AssessmentPeriod] = mapped_column(
        String(10), nullable=False, default=AssessmentPeriod.monthly
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="carbon_assessments")
    emission_inputs: Mapped["EmissionInputs"] = relationship(
        "EmissionInputs", back_populates="assessment", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_carbon_assessments_user_id", "user_id"),
        Index("ix_carbon_assessments_period", "assessment_period"),
        Index("ix_carbon_assessments_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<CarbonAssessment id={self.id} user_id={self.user_id} "
            f"total={self.total_emission}>"
        )
