"""
Database seeding script for Carbon Factor reference data.

Seeds the carbon_factors table with official emission factors from IPCC/EPA:
- Transport (car, motorcycle, bus, train, flight, bicycle)
- Energy (electricity India grid, ac_per_hour, lpg_per_kg)
- Food (vegetarian, mixed, non_vegetarian)
- Waste (recycling score, plastic score)
"""
import logging
import uuid
from datetime import date
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.carbon_factor import CarbonFactor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_carbon_factors(db: Session) -> None:
    """
    Idempotently seed the carbon_factors table with reference data.
    """
    logger.info("Starting carbon factors seeding...")

    factors_data = [
        # 1. Transportation (kg CO₂e / km)
        {
            "category": "transport",
            "sub_category": "car",
            "factor_value": 0.192,
            "unit": "kg CO₂e / km",
        },
        {
            "category": "transport",
            "sub_category": "motorcycle",
            "factor_value": 0.113,
            "unit": "kg CO₂e / km",
        },
        {
            "category": "transport",
            "sub_category": "bus",
            "factor_value": 0.089,
            "unit": "kg CO₂e / km",
        },
        {
            "category": "transport",
            "sub_category": "train",
            "factor_value": 0.041,
            "unit": "kg CO₂e / km",
        },
        {
            "category": "transport",
            "sub_category": "flight",
            "factor_value": 0.255,
            "unit": "kg CO₂e / km",
        },
        {
            "category": "transport",
            "sub_category": "bicycle",
            "factor_value": 0.000,
            "unit": "kg CO₂e / km",
        },

        # 2. Energy
        {
            "category": "energy",
            "sub_category": "electricity",
            "factor_value": 0.820,
            "unit": "kg CO₂e / kWh",  # India grid
        },
        {
            "category": "energy",
            "sub_category": "ac",
            "factor_value": 0.150,
            "unit": "kg CO₂e / hour",
        },
        {
            "category": "energy",
            "sub_category": "lpg",
            "factor_value": 2.980,
            "unit": "kg CO₂e / kg",
        },

        # 3. Food (kg CO₂e / day)
        {
            "category": "food",
            "sub_category": "vegetarian",
            "factor_value": 1.700,
            "unit": "kg CO₂e / day",
        },
        {
            "category": "food",
            "sub_category": "mixed",
            "factor_value": 2.500,
            "unit": "kg CO₂e / day",
        },
        {
            "category": "food",
            "sub_category": "non_vegetarian",
            "factor_value": 3.300,
            "unit": "kg CO₂e / day",
        },

        # 4. Waste (kg CO₂e / score index)
        {
            "category": "waste",
            "sub_category": "plastic",
            "factor_value": 15.000,
            "unit": "kg CO₂e / score",
        },
        {
            "category": "waste",
            "sub_category": "recycling",
            "factor_value": 5.000,
            "unit": "kg CO₂e / score",
        },
    ]

    effective_dt = date(2024, 1, 1)

    for data in factors_data:
        # Check if record already exists
        existing = (
            db.query(CarbonFactor)
            .filter(
                CarbonFactor.category == data["category"],
                CarbonFactor.sub_category == data["sub_category"]
            )
            .first()
        )

        if existing:
            logger.info(
                f"Updating existing factor for {data['category']}/{data['sub_category']}"
            )
            existing.factor_value = data["factor_value"]
            existing.unit = data["unit"]
            existing.source_name = "IPCC/EPA"
            existing.version = "v1.0"
            existing.effective_date = effective_dt
        else:
            logger.info(
                f"Creating new factor for {data['category']}/{data['sub_category']}"
            )
            factor = CarbonFactor(
                id=uuid.uuid4(),
                category=data["category"],
                sub_category=data["sub_category"],
                factor_value=data["factor_value"],
                unit=data["unit"],
                source_name="IPCC/EPA",
                version="v1.0",
                effective_date=effective_dt,
            )
            db.add(factor)

    db.commit()
    logger.info("Carbon factors successfully seeded.")


if __name__ == "__main__":
    db_session = SessionLocal()
    try:
        seed_carbon_factors(db_session)
    finally:
        db_session.close()
