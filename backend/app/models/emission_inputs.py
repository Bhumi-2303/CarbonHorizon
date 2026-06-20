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

    # Transport Extended
    vehicle_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    fuel_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    trips_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    public_transport_usage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    carpooling_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    air_travel_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    train_travel_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    walking_cycling_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Energy Extended
    energy_efficiency_rating: Mapped[str | None] = mapped_column(String(50), nullable=True)
    heating_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Food & Waste Extended
    local_food_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    food_waste_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)
    composting_frequency: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ewaste_disposal_method: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Water
    daily_water_liters: Mapped[float | None] = mapped_column(Float, nullable=True)
    shower_duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    water_heating_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Housing
    house_size_sqm: Mapped[float | None] = mapped_column(Float, nullable=True)
    home_insulation_level: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Digital
    screen_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    streaming_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    gaming_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Shopping
    new_clothes_monthly: Mapped[int | None] = mapped_column(Integer, nullable=True)
    second_hand_purchases: Mapped[str | None] = mapped_column(String(50), nullable=True)
    electronics_purchases_yearly: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Occupation / Lifestyle
    commute_days_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)
    remote_work_percentage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Geographic
    assessment_country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assessment_state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    assessment_city: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Offsets (Category 12 equivalent)
    composting_active: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    tree_planting_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reusable_products_usage: Mapped[str | None] = mapped_column(String(50), nullable=True)
    green_transport_choices: Mapped[bool | None] = mapped_column(Boolean, nullable=True)

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
