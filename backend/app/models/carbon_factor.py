"""
CarbonFactor ORM model.

Table: carbon_factors
- UUID PK
- Official emission factor reference data (IPCC, GHG Protocol, etc.)
- Version-controlled via 'version' + 'effective_date'
- Indexes: category, sub_category (both from schema doc)
"""
import uuid
from datetime import date

from sqlalchemy import Date, DateTime, Float, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.mixins import CreatedAtMixin
from sqlalchemy import func


class CarbonFactor(Base, CreatedAtMixin):
    __tablename__ = "carbon_factors"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )

    # Classification
    category: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # e.g. "transport", "energy"
    sub_category: Mapped[str | None] = mapped_column(
        String(100), nullable=True
    )  # e.g. "car", "electricity_grid"

    # Factor
    factor_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(50), nullable=False)  # e.g. "kg CO₂e / km"

    # Provenance
    source_reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    effective_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Last updated (separate from created_at — factors can be revised)
    updated_at: Mapped[None] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=True,
    )

    __table_args__ = (
        Index("ix_carbon_factors_category", "category"),           # schema doc requirement
        Index("ix_carbon_factors_sub_category", "sub_category"),   # schema doc requirement
        Index("ix_carbon_factors_version", "version"),
        Index("ix_carbon_factors_effective_date", "effective_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<CarbonFactor id={self.id} category={self.category!r} "
            f"sub={self.sub_category!r} value={self.factor_value} {self.unit}>"
        )
