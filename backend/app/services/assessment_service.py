"""
AssessmentService — carbon assessment management business logic.

Handles creating carbon footprint assessments, persisting raw user inputs
along with calculated emissions, and querying assessment history.
"""
import uuid
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.carbon_assessment import CarbonAssessment
from app.models.emission_inputs import EmissionInputs
from app.schemas.assessment import AssessmentInputs
from app.services import calculation_engine


def _get_val(obj, key, default=None):
    """
    Helper to extract a field from a dictionary or object (ORM model / Pydantic schema).
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _map_to_dict(assessment: CarbonAssessment) -> dict:
    """
    Map CarbonAssessment ORM fields to the schema-conforming dictionary format.
    """
    return {
        "assessment_id": assessment.id,
        "total_emission": assessment.total_emission,
        "transport": assessment.transport_emission,
        "energy": assessment.energy_emission,
        "food": assessment.food_emission,
        "waste": assessment.waste_emission,
        "housing": assessment.housing_emission or 0.0,
        "water": assessment.water_emission or 0.0,
        "digital": assessment.digital_emission or 0.0,
        "shopping": assessment.shopping_emission or 0.0,
        "offsets": assessment.offsets_total or 0.0,
        "carbon_score": assessment.carbon_score,
        "assessment_period": assessment.assessment_period,
        "created_at": assessment.created_at,
    }


class AssessmentService:

    @staticmethod
    def create_assessment(
        db: Session,
        user_id: uuid.UUID,
        inputs: AssessmentInputs
    ) -> dict:
        """
        Calculate user footprint using the calculation engine, save both the
        breakdown (carbon_assessments) and the raw inputs (emission_inputs) to DB,
        and return the mapped response fields.
        """
        # Run calculations using backend calculation engine
        results = calculation_engine.calculate_total_emissions(db, inputs)

        period = _get_val(inputs, "assessment_period", "monthly")

        # Build CarbonAssessment record
        assessment = CarbonAssessment(
            user_id=user_id,
            transport_emission=results["transport_emission"],
            energy_emission=results["energy_emission"],
            food_emission=results["food_emission"],
            waste_emission=results["waste_emission"],
            housing_emission=results.get("housing_emission", 0.0),
            water_emission=results.get("water_emission", 0.0),
            digital_emission=results.get("digital_emission", 0.0),
            shopping_emission=results.get("shopping_emission", 0.0),
            offsets_total=results.get("offsets_total", 0.0),
            total_emission=results["total_emission"],
            carbon_score=results["carbon_score"],
            calculation_version=results["calculation_version"],
            factor_version=results["factor_version"],
            assessment_period=period
        )
        db.add(assessment)
        db.flush()  # Populate the generated assessment ID

        # Build raw inputs record linked to the assessment
        inputs_record = EmissionInputs(
            assessment_id=assessment.id,
            transport_mode=_get_val(inputs, "transport_mode"),
            distance_km=_get_val(inputs, "distance_km"),
            electricity_kwh=_get_val(inputs, "electricity_kwh"),
            ac_hours=_get_val(inputs, "ac_hours"),
            lpg_usage=_get_val(inputs, "lpg_usage"),
            solar_usage=_get_val(inputs, "solar_usage"),
            diet_type=_get_val(inputs, "diet_type"),
            recycling_score=_get_val(inputs, "recycling_score"),
            plastic_usage_score=_get_val(inputs, "plastic_usage_score"),
            household_size=_get_val(inputs, "household_size"),

            vehicle_type=_get_val(inputs, "vehicle_type"),
            fuel_type=_get_val(inputs, "fuel_type"),
            trips_per_week=_get_val(inputs, "trips_per_week"),
            public_transport_usage=_get_val(inputs, "public_transport_usage"),
            carpooling_frequency=_get_val(inputs, "carpooling_frequency"),
            air_travel_frequency=_get_val(inputs, "air_travel_frequency"),
            train_travel_frequency=_get_val(inputs, "train_travel_frequency"),
            walking_cycling_hours=_get_val(inputs, "walking_cycling_hours"),

            energy_efficiency_rating=_get_val(inputs, "energy_efficiency_rating"),
            heating_type=_get_val(inputs, "heating_type"),

            local_food_frequency=_get_val(inputs, "local_food_frequency"),
            food_waste_percentage=_get_val(inputs, "food_waste_percentage"),
            composting_frequency=_get_val(inputs, "composting_frequency"),
            ewaste_disposal_method=_get_val(inputs, "ewaste_disposal_method"),

            daily_water_liters=_get_val(inputs, "daily_water_liters"),
            shower_duration_minutes=_get_val(inputs, "shower_duration_minutes"),
            water_heating_type=_get_val(inputs, "water_heating_type"),

            house_size_sqm=_get_val(inputs, "house_size_sqm"),
            home_insulation_level=_get_val(inputs, "home_insulation_level"),

            screen_time_hours=_get_val(inputs, "screen_time_hours"),
            streaming_hours=_get_val(inputs, "streaming_hours"),
            gaming_hours=_get_val(inputs, "gaming_hours"),

            new_clothes_monthly=_get_val(inputs, "new_clothes_monthly"),
            second_hand_purchases=_get_val(inputs, "second_hand_purchases"),
            electronics_purchases_yearly=_get_val(inputs, "electronics_purchases_yearly"),

            commute_days_per_week=_get_val(inputs, "commute_days_per_week"),
            remote_work_percentage=_get_val(inputs, "remote_work_percentage"),

            assessment_country=_get_val(inputs, "assessment_country"),
            assessment_state=_get_val(inputs, "assessment_state"),
            assessment_city=_get_val(inputs, "assessment_city"),

            composting_active=_get_val(inputs, "composting_active"),
            tree_planting_count=_get_val(inputs, "tree_planting_count"),
            reusable_products_usage=_get_val(inputs, "reusable_products_usage"),
            green_transport_choices=_get_val(inputs, "green_transport_choices")
        )
        db.add(inputs_record)
        db.commit()
        db.refresh(assessment)

        return _map_to_dict(assessment)

    @staticmethod
    def get_assessment_history(db: Session, user_id: uuid.UUID) -> list[dict]:
        """
        Fetch all past carbon assessments for the user in descending chronological order.
        """
        assessments = (
            db.query(CarbonAssessment)
            .filter(CarbonAssessment.user_id == user_id)
            .order_by(CarbonAssessment.created_at.desc())
            .all()
        )
        return [_map_to_dict(a) for a in assessments]

    @staticmethod
    def get_assessment_by_id(
        db: Session,
        user_id: uuid.UUID,
        assessment_id: uuid.UUID
    ) -> dict:
        """
        Retrieve a specific carbon assessment, verifying that it belongs to the requesting user.
        Raises HTTP 404 if the assessment is not found or is owned by someone else.
        """
        assessment = (
            db.query(CarbonAssessment)
            .filter(
                CarbonAssessment.user_id == user_id,
                CarbonAssessment.id == assessment_id
            )
            .first()
        )
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        return _map_to_dict(assessment)

    @staticmethod
    def get_latest_assessment(db: Session, user_id: uuid.UUID) -> dict:
        """
        Retrieve the user's most recent carbon assessment.
        Raises HTTP 404 if no assessments exist for the user.
        """
        assessment = (
            db.query(CarbonAssessment)
            .filter(CarbonAssessment.user_id == user_id)
            .order_by(CarbonAssessment.created_at.desc())
            .first()
        )
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No assessments found for this user"
            )
        return _map_to_dict(assessment)

    @staticmethod
    def delete_assessment(
        db: Session,
        user_id: uuid.UUID,
        assessment_id: uuid.UUID
    ) -> None:
        """
        Delete a carbon assessment, verifying ownership.
        Raises HTTP 404 if not found or unauthorized.
        """
        assessment = (
            db.query(CarbonAssessment)
            .filter(
                CarbonAssessment.user_id == user_id,
                CarbonAssessment.id == assessment_id
            )
            .first()
        )
        if not assessment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assessment not found"
            )
        db.delete(assessment)
        db.commit()
