"""
tests/test_unit_assessment.py
================================
Unit tests for app.services.assessment_service.
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.carbon_assessment import CarbonAssessment
from app.models.emission_inputs import EmissionInputs
from app.models.enums import TransportMode, DietType, AssessmentPeriod
from app.schemas.assessment import AssessmentInputs
from app.services.assessment_service import AssessmentService


class TestAssessmentService:

    def test_create_assessment_success(self, db: Session, make_user):
        """create_assessment calculates emissions, saves to tables, and returns mapped dict."""
        user = make_user()
        inputs = AssessmentInputs(
            transport_mode=TransportMode.car,
            distance_km=150.0,
            electricity_kwh=200.0,
            ac_hours=12.0,
            lpg_usage=4.0,
            solar_usage=False,
            diet_type=DietType.vegetarian,
            recycling_score=2,
            plastic_usage_score=4,
            household_size=3,
            assessment_period=AssessmentPeriod.monthly
        )

        result = AssessmentService.create_assessment(db, user.id, inputs)

        # Assert returned data structure
        assert "assessment_id" in result
        assert result["total_emission"] > 0
        assert result["transport"] == 150.0 * 0.18  # car default fallback
        assert result["energy"] == (200.0 * 0.5) + (12.0 * 0.8) + (4.0 * 3.0)
        assert result["food"] == 150.0 / 3
        assert result["waste"] == (4 * 15.0) - (2 * 5.0)
        assert result["carbon_score"] > 0
        assert result["assessment_period"] == AssessmentPeriod.monthly

        # Assert persisted records
        assessment_in_db = db.query(CarbonAssessment).filter(CarbonAssessment.id == result["assessment_id"]).first()
        assert assessment_in_db is not None
        assert assessment_in_db.user_id == user.id
        assert assessment_in_db.total_emission == result["total_emission"]

        inputs_in_db = db.query(EmissionInputs).filter(EmissionInputs.assessment_id == result["assessment_id"]).first()
        assert inputs_in_db is not None
        assert inputs_in_db.transport_mode == "car"
        assert inputs_in_db.distance_km == 150.0
        assert inputs_in_db.household_size == 3

    def test_get_assessment_history(self, db: Session, make_user):
        """get_assessment_history retrieves all assessments for the user in desc chronological order."""
        user1 = make_user()
        user2 = make_user()

        # Add assessments for user1
        inputs = AssessmentInputs(diet_type=DietType.mixed)
        res1 = AssessmentService.create_assessment(db, user1.id, inputs)
        
        # Manually alter created_at of res1 to be older to prevent SQLite timestamp collisions
        a1 = db.query(CarbonAssessment).filter(CarbonAssessment.id == res1["assessment_id"]).first()
        a1.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()

        res2 = AssessmentService.create_assessment(db, user1.id, inputs)

        # Add assessment for user2
        AssessmentService.create_assessment(db, user2.id, inputs)

        # Query user1 history
        history = AssessmentService.get_assessment_history(db, user1.id)
        assert len(history) == 2
        # Descending chronological order
        assert history[0]["assessment_id"] == res2["assessment_id"]
        assert history[1]["assessment_id"] == res1["assessment_id"]

    def test_get_assessment_by_id_success(self, db: Session, make_user):
        """get_assessment_by_id retrieves specific assessment owned by user."""
        user = make_user()
        inputs = AssessmentInputs(diet_type=DietType.mixed)
        created = AssessmentService.create_assessment(db, user.id, inputs)

        fetched = AssessmentService.get_assessment_by_id(db, user.id, created["assessment_id"])
        assert fetched["assessment_id"] == created["assessment_id"]
        assert fetched["total_emission"] == created["total_emission"]

    def test_get_assessment_by_id_not_found(self, db: Session, make_user):
        """get_assessment_by_id raises HTTP 404 if assessment does not exist."""
        user = make_user()
        random_id = uuid.uuid4()
        with pytest.raises(HTTPException) as exc:
            AssessmentService.get_assessment_by_id(db, user.id, random_id)
        assert exc.value.status_code == 404

    def test_get_assessment_by_id_unauthorized(self, db: Session, make_user):
        """get_assessment_by_id raises HTTP 404 if assessment belongs to another user."""
        user1 = make_user()
        user2 = make_user()
        inputs = AssessmentInputs(diet_type=DietType.mixed)
        created = AssessmentService.create_assessment(db, user1.id, inputs)

        # user2 attempts to read user1's assessment
        with pytest.raises(HTTPException) as exc:
            AssessmentService.get_assessment_by_id(db, user2.id, created["assessment_id"])
        assert exc.value.status_code == 404

    def test_get_latest_assessment_success(self, db: Session, make_user):
        """get_latest_assessment fetches the most recent assessment."""
        user = make_user()
        inputs = AssessmentInputs(diet_type=DietType.mixed)
        res1 = AssessmentService.create_assessment(db, user.id, inputs)
        
        # Manually alter created_at of res1 to be older to prevent SQLite timestamp collisions
        a1 = db.query(CarbonAssessment).filter(CarbonAssessment.id == res1["assessment_id"]).first()
        a1.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()

        latest = AssessmentService.create_assessment(db, user.id, inputs)

        fetched = AssessmentService.get_latest_assessment(db, user.id)
        assert fetched["assessment_id"] == latest["assessment_id"]

    def test_get_latest_assessment_not_found(self, db: Session, make_user):
        """get_latest_assessment raises HTTP 404 if user has no assessments."""
        user = make_user()
        with pytest.raises(HTTPException) as exc:
            AssessmentService.get_latest_assessment(db, user.id)
        assert exc.value.status_code == 404

    def test_delete_assessment_success(self, db: Session, make_user):
        """delete_assessment deletes the record from DB if owned by user."""
        user = make_user()
        inputs = AssessmentInputs(diet_type=DietType.mixed)
        created = AssessmentService.create_assessment(db, user.id, inputs)

        # Ensure exists
        assert db.query(CarbonAssessment).filter(CarbonAssessment.id == created["assessment_id"]).first() is not None

        AssessmentService.delete_assessment(db, user.id, created["assessment_id"])

        # Ensure deleted
        assert db.query(CarbonAssessment).filter(CarbonAssessment.id == created["assessment_id"]).first() is None

    def test_delete_assessment_unauthorized_raises_404(self, db: Session, make_user):
        """delete_assessment raises HTTP 404 if attempting to delete another user's assessment."""
        user1 = make_user()
        user2 = make_user()
        inputs = AssessmentInputs(diet_type=DietType.mixed)
        created = AssessmentService.create_assessment(db, user1.id, inputs)

        with pytest.raises(HTTPException) as exc:
            AssessmentService.delete_assessment(db, user2.id, created["assessment_id"])
        assert exc.value.status_code == 404

    def test_create_assessment_none_inputs(self, db: Session, make_user):
        """create_assessment handles a None inputs payload by using fallbacks."""
        user = make_user()
        result = AssessmentService.create_assessment(db, user.id, None)
        assert result["total_emission"] == 0.0
        assert result["carbon_score"] == 100

