"""
Emission ORM model — no logic yet.
Tracks individual carbon emission records per organization.
"""
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Emission(Base):
    __tablename__ = "emissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    organization_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(255), nullable=False)  # e.g. "electricity", "transport"
    scope: Mapped[int] = mapped_column(Integer, nullable=False)        # 1, 2, or 3
    quantity_kg_co2e: Mapped[float] = mapped_column(Float, nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    notes: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self) -> str:
        return f"<Emission id={self.id} scope={self.scope} kg_co2e={self.quantity_kg_co2e}>"
