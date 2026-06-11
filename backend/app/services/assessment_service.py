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
            household_size=_get_val(inputs, "household_size")
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
