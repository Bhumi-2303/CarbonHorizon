"""
Database initialization and seeding module.
Idempotently seeds reference data:
- Carbon Factors (IPCC/EPA factors)
- Habit Definitions (predefined eco-habits)
"""
from __future__ import annotations

import os
import sys
import logging
from typing import Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
_BACKEND_ROOT = os.path.dirname(os.path.dirname(_HERE))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.seed_carbon_factors import seed_carbon_factors
from app.models.habit_definition import HabitDefinition

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_habit_definitions(db: Session, *, commit: bool = True) -> None:
    """
    Idempotently seed the habit_definitions table.
    """
    logger.info("Starting habit definitions seeding...")
    definitions = [
        {"habit_type": "public_transport", "factor": 1.2, "unit": "kg CO2e"},
        {"habit_type": "recycling", "factor": 0.5, "unit": "kg CO2e"},
        {"habit_type": "save_electricity", "factor": 0.8, "unit": "kg CO2e"},
        {"habit_type": "water_conservation", "factor": 0.3, "unit": "kg CO2e"},
        {"habit_type": "plastic_reduction", "factor": 0.4, "unit": "kg CO2e"},
    ]

    for d in definitions:
        existing = (
            db.query(HabitDefinition)
            .filter(HabitDefinition.habit_type == d["habit_type"])
            .first()
        )
        if not existing:
            new_def = HabitDefinition(
                habit_type=d["habit_type"],
                carbon_saving_factor=d["factor"],
                unit=d["unit"],
            )
            db.add(new_def)

    if commit:
        db.commit()
    logger.info("Habit definitions successfully seeded.")


def init_db(db: Optional[Session] = None) -> None:
    """
    Seed all required reference data within a single transaction.
    """
    session = db
    close_after = False
    if session is None:
        session = SessionLocal()
        close_after = True

    try:
        seed_carbon_factors(session, commit=False)
        seed_habit_definitions(session, commit=False)
        session.commit()
        logger.info("All reference data initialized successfully.")
    except Exception as e:
        logger.error(f"Error during reference data seeding: {e}")
        session.rollback()
        raise
    finally:
        if close_after:
            session.close()


if __name__ == "__main__":
    init_db()
