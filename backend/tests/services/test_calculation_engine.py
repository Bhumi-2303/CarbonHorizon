"""
tests/test_unit_calculation.py
================================
Unit tests for app.services.calculation_engine.

Tests core calculations, database lookup logic, fallback constants,
and carbon score normalization/clamping.
"""
import pytest
from sqlalchemy.orm import Session
from app.models.carbon_factor import CarbonFactor
from app.models.enums import TransportMode, DietType, AssessmentPeriod
from app.services import calculation_engine


# Helper class to mock object inputs (like ORM model/Pydantic schemas)
class DummyEmissionInput:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Transport calculations
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateTransport:

    def test_transport_no_inputs(self):
        """calculate_transport returns 0.0 when mode or distance is missing."""
        assert calculation_engine.calculate_transport(None, 100.0) == 0.0
        assert calculation_engine.calculate_transport("car", None) == 0.0
        assert calculation_engine.calculate_transport("", 100.0) == 0.0

    def test_transport_negative_distance(self):
        """calculate_transport clamps negative distances to 0.0."""
        assert calculation_engine.calculate_transport("car", -50.0) == 0.0

    def test_transport_fallbacks_when_no_db(self):
        """calculate_transport uses standard fallback values when db is None."""
        # Car fallback = 0.18
        assert calculation_engine.calculate_transport("car", 100.0) == 18.0
        # Bicycle fallback = 0.00
        assert calculation_engine.calculate_transport("bicycle", 100.0) == 0.0
        # Unknown fallback = 0.10
        assert calculation_engine.calculate_transport("rocket", 100.0) == 10.0

    def test_transport_db_lookup(self, db: Session):
        """calculate_transport successfully queries carbon_factors from DB."""
        factor = CarbonFactor(
            category="transport",
            sub_category="car",
            factor_value=0.42,
            unit="kg CO₂e / km",
            version="TEST-V1"
        )
        db.add(factor)
        db.flush()

        version_tracker = {}
        result = calculation_engine.calculate_transport(
            transport_mode="car",
            distance_km=100.0,
            db=db,
            version_tracker=version_tracker
        )

        assert result == 42.0
        assert version_tracker.get("factor_version") == "TEST-V1"

    def test_transport_db_query_fails_gracefully(self, db: Session):
        """calculate_transport falls back to defaults if DB query fails."""
        # Pass a mocked db that throws an exception when queried
        class BrokenDB:
            def query(self, *args, **kwargs):
                raise Exception("DB is down")

        # Should fall back to 0.18 for car instead of crashing
        result = calculation_engine.calculate_transport("car", 100.0, db=BrokenDB())
        assert result == 18.0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Energy calculations
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateEnergy:

    def test_energy_basic(self):
        """calculate_energy computes basic values using fallback constants."""
        # 100 kWh * 0.50 + 10 hrs * 0.80 + 5 kg * 3.00 = 50.0 + 8.0 + 15.0 = 73.0
        result = calculation_engine.calculate_energy(
            electricity_kwh=100.0,
            ac_hours=10.0,
            lpg_usage=5.0,
            solar_usage=False
        )
        assert result == 73.0

    def test_energy_solar_offset(self):
        """solar_usage=True completely offsets electricity emissions."""
        # 100 kWh is offset to 0. AC and LPG still calculate.
        # 0.0 + 10 hrs * 0.80 + 5 kg * 3.00 = 8.0 + 15.0 = 23.0
        result = calculation_engine.calculate_energy(
            electricity_kwh=100.0,
            ac_hours=10.0,
            lpg_usage=5.0,
            solar_usage=True
        )
        assert result == 23.0

    def test_energy_none_values(self):
        """calculate_energy treats None values as 0.0."""
        assert calculation_engine.calculate_energy(None, None, None, False) == 0.0
        assert calculation_engine.calculate_energy(100.0, None, None, False) == 50.0

    def test_energy_negative_values(self):
        """calculate_energy clamps negative inputs to 0.0."""
        result = calculation_engine.calculate_energy(
            electricity_kwh=-10.0,
            ac_hours=-5.0,
            lpg_usage=-2.0,
            solar_usage=False
        )
        assert result == 0.0

    def test_energy_db_lookup(self, db: Session):
        """calculate_energy queries DB factors correctly."""
        db.add(CarbonFactor(category="energy", sub_category="electricity", factor_value=0.2, unit="kg/kWh", version="V2"))
        db.add(CarbonFactor(category="energy", sub_category="ac", factor_value=0.4, unit="kg/hr", version="V2"))
        db.add(CarbonFactor(category="energy", sub_category="lpg", factor_value=1.5, unit="kg/kg", version="V2"))
        db.flush()

        version_tracker = {}
        result = calculation_engine.calculate_energy(
            electricity_kwh=100.0,
            ac_hours=10.0,
            lpg_usage=5.0,
            solar_usage=False,
            db=db,
            version_tracker=version_tracker
        )
        # 100 * 0.2 + 10 * 0.4 + 5 * 1.5 = 20.0 + 4.0 + 7.5 = 31.5
        assert result == 31.5
        assert version_tracker.get("factor_version") == "V2"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Food calculations
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateFood:

    def test_food_no_inputs(self):
        """calculate_food returns 0.0 when diet type is empty or missing."""
        assert calculation_engine.calculate_food(None, 4) == 0.0
        assert calculation_engine.calculate_food("", 4) == 0.0

    def test_food_diet_types_fallbacks(self):
        """calculate_food uses standard fallback values for diets."""
        # Vegetarian: 1.7 * 30 / 1 = 51.0
        assert calculation_engine.calculate_food("vegetarian", 1) == 51.0
        # Mixed: 2.5 * 30 / 1 = 75.0
        assert calculation_engine.calculate_food("mixed", 1) == 75.0
        # Non-vegetarian: 3.3 * 30 / 1 = 99.0
        assert calculation_engine.calculate_food("non_vegetarian", None) == 99.0

    def test_food_household_division(self):
        """calculate_food does not divide diet emissions by household size."""
        # Non-vegetarian = 3.3 * 30 = 99.0
        assert calculation_engine.calculate_food("non_vegetarian", 4) == 99.0
        # Mixed = 2.5 * 30 = 75.0
        assert calculation_engine.calculate_food(DietType.mixed, 2) == 75.0

    def test_food_invalid_household_size(self):
        """calculate_food defaults household_size to 1 if <= 0 or None."""
        assert calculation_engine.calculate_food("vegetarian", 0) == 51.0
        assert calculation_engine.calculate_food("vegetarian", -5) == 51.0

    def test_food_db_lookup(self, db: Session):
        """calculate_food queries DB factors correctly."""
        db.add(CarbonFactor(category="food", sub_category="vegetarian", factor_value=1.5, unit="kg", version="FOOD-V1"))
        db.flush()

        result = calculation_engine.calculate_food("vegetarian", 3, db=db)
        # 1.5 * 30 = 45.0
        assert result == 45.0

    def test_food_assessment_periods(self):
        """calculate_food scales daily diet factors based on assessment period (daily/monthly/annual)."""
        # Daily: vegetarian = 1.7 * 1 / 1 = 1.7
        assert calculation_engine.calculate_food("vegetarian", 1, assessment_period="daily") == 1.7
        # Annual: vegetarian = 1.7 * 365 / 1 = 620.5
        assert calculation_engine.calculate_food("vegetarian", 1, assessment_period=AssessmentPeriod.annual) == 620.5


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Waste calculations
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateWaste:

    def test_waste_no_inputs(self):
        """calculate_waste returns 0.0 when both scores are None."""
        assert calculation_engine.calculate_waste(None, None) == 0.0

    def test_waste_basic(self):
        """calculate_waste computes emissions based on recycling and plastic scores."""
        # plastic score=3 (3 * 15.0 = 45.0), recycling score=1 (1 * 5.0 = 5.0) -> 40.0
        assert calculation_engine.calculate_waste(1, 3) == 40.0

    def test_waste_clamped_to_zero(self):
        """waste emissions cannot go negative (e.g. extremely high recycling)."""
        # plastic score=1 (15.0), recycling score=5 (25.0) -> -10.0 clamped to 0.0
        assert calculation_engine.calculate_waste(5, 1) == 0.0

    def test_waste_one_score_none(self):
        """None scores are treated as 0."""
        # plastic score=2 (30.0), recycling score=None (0.0) -> 30.0
        assert calculation_engine.calculate_waste(None, 2) == 30.0
        # plastic score=None (0.0), recycling score=2 (10.0) -> -10.0 clamped to 0.0
        assert calculation_engine.calculate_waste(2, None) == 0.0

    def test_waste_db_lookup(self, db: Session):
        """calculate_waste queries DB factors correctly."""
        db.add(CarbonFactor(category="waste", sub_category="plastic", factor_value=10.0, unit="kg", version="WASTE-V2"))
        db.add(CarbonFactor(category="waste", sub_category="recycling", factor_value=2.0, unit="kg", version="WASTE-V2"))
        db.flush()

        result = calculation_engine.calculate_waste(3, 5, db=db)
        # 5 * 10 - 3 * 2 = 50 - 6 = 44.0
        assert result == 44.0


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Total emissions and carbon score
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalculateTotalEmissions:

    def test_total_emissions_dict_input(self):
        """calculate_total_emissions parses dictionaries correctly."""
        payload = {
            "transport_mode": "car",
            "distance_km": 100.0,          # 18.0
            "electricity_kwh": 100.0,      # 50.0
            "ac_hours": 10.0,              # 8.0
            "lpg_usage": 5.0,              # 15.0
            "solar_usage": False,
            "diet_type": "vegetarian",     # 1.7 * 30 = 51.0
            "household_size": 2,
            "recycling_score": 1,          # 3 * 15 - 1 * 5 = 40.0
            "plastic_usage_score": 3,
        }
        # Total: 18.0 + (50.0 + 8.0 + 15.0) + 51.0 + 40.0 = 18 + 73 + 51.0 + 40 = 182.0
        # Score: 100 - (182.0 / 1000.0) * 100 = 100 - 18.2 = 81.8 -> round to 82.
        result = calculation_engine.calculate_total_emissions(db=None, emission_input=payload)

        assert result["transport_emission"] == 18.0
        assert result["energy_emission"] == 73.0
        assert result["food_emission"] == 51.0
        assert result["waste_emission"] == 40.0
        assert result["total_emission"] == 182.0
        assert result["carbon_score"] == 82
        assert result["calculation_version"] == "1.0.0"
        assert result["factor_version"] == "IPCC-2024"

    def test_total_emissions_object_input(self):
        """calculate_total_emissions parses object classes correctly (ORM/Pydantic schemas)."""
        payload = DummyEmissionInput(
            transport_mode="car",
            distance_km=100.0,
            electricity_kwh=100.0,
            ac_hours=10.0,
            lpg_usage=5.0,
            solar_usage=False,
            diet_type="vegetarian",
            household_size=2,
            recycling_score=1,
            plastic_usage_score=3,
        )
        result = calculation_engine.calculate_total_emissions(db=None, emission_input=payload)
        assert result["total_emission"] == 182.0

    def test_signature_overloads(self):
        """calculate_total_emissions supports running with and without DB parameters."""
        payload = {
            "transport_mode": "car",
            "distance_km": 100.0,
        }
        # Direct: calculate_total_emissions(payload)
        res1 = calculation_engine.calculate_total_emissions(payload)
        assert res1["total_emission"] == 18.0

        # With DB: calculate_total_emissions(None, payload)
        res2 = calculation_engine.calculate_total_emissions(None, payload)
        assert res2["total_emission"] == 18.0

    def test_score_clamping(self):
        """Carbon score clamps between 0 and 100."""
        # 1. Extremely clean lifestyle -> 0 emissions -> score 100
        res_zero = calculation_engine.calculate_total_emissions({
            "transport_mode": "bicycle",
            "distance_km": 0.0,
            "diet_type": None,
        })
        assert res_zero["total_emission"] == 0.0
        assert res_zero["carbon_score"] == 100

        # 2. Extremely dirty lifestyle -> massive emissions -> score clamps to 0
        res_huge = calculation_engine.calculate_total_emissions({
            "transport_mode": "flight",
            "distance_km": 10000.0,  # 2500 kg
            "electricity_kwh": 5000.0,  # 2500 kg
        })
        assert res_huge["total_emission"] == 5000.0
        assert res_huge["carbon_score"] == 0

    def test_none_input(self):
        """calculate_total_emissions handles a None emission_input by defaulting all fields."""
        result = calculation_engine.calculate_total_emissions(None)
        assert result["total_emission"] == 0.0
        assert result["carbon_score"] == 100
        assert result["calculation_version"] == "1.0.0"

