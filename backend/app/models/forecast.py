"""
Forecast ORM model.

Table: forecasts
- UUID PK
- Forecast session (header record)
- forecast_type ENUM
- Index: user_id
"""
import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin
from app.models.enums import ForecastType


class Forecast(Base, TimestampMixin):
    __tablename__ = "forecasts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    forecast_type: Mapped[ForecastType] = mapped_column(
        String(20), nullable=False, default=ForecastType.current_path
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="forecasts")
    forecast_points: Mapped[list["ForecastPoint"]] = relationship(
        "ForecastPoint", back_populates="forecast", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_forecasts_user_id", "user_id"),
        Index("ix_forecasts_type", "forecast_type"),
    )

    def __repr__(self) -> str:
        return f"<Forecast id={self.id} user_id={self.user_id} type={self.forecast_type!r}>"
