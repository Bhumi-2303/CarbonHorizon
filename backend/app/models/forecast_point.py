"""
ForecastPoint ORM model.

Table: forecast_points
- UUID PK
- Append-only detail rows for a Forecast session
- Supports unlimited time horizons (3m, 6m, 12m, 24m, …)
- Index: forecast_id
"""
import uuid

from sqlalchemy import Float, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin


class ForecastPoint(Base, CreatedAtMixin):
    __tablename__ = "forecast_points"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    forecast_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("forecasts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # e.g. 3, 6, 12, 24 — months from assessment date
    month_offset: Mapped[int] = mapped_column(Integer, nullable=False)
    predicted_emission: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationship
    forecast: Mapped["Forecast"] = relationship("Forecast", back_populates="forecast_points")

    __table_args__ = (
        Index("ix_forecast_points_forecast_id", "forecast_id"),
        Index("ix_forecast_points_month_offset", "forecast_id", "month_offset"),
    )

    def __repr__(self) -> str:
        return (
            f"<ForecastPoint id={self.id} forecast_id={self.forecast_id} "
            f"month={self.month_offset} emission={self.predicted_emission}>"
        )
