"""
tests/test_integration_assessment.py
================================
HTTP integration tests for the /api/v1/assessment/* endpoints.
"""
import uuid
import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.carbon_assessment import CarbonAssessment
from app.models.enums import TransportMode, DietType, AssessmentPeriod
from app.services.assessment_service import AssessmentService


class TestAssessmentEndpoints:

    # ═══════════════════════════════════════════════════════════════════════════
    # POST /api/v1/assessment/create
    # ═══════════════════════════════════════════════════════════════════════════

    def test_create_assessment_success(self, client: TestClient, auth_headers: dict):
        """POST /create creates an assessment and returns standard success envelope."""
        payload = {
            "transport_mode": "car",
            "distance_km": 150.0,
            "electricity_kwh": 200.0,
            "ac_hours": 12.0,
            "lpg_usage": 4.0,
            "solar_usage": False,
            "diet_type": "vegetarian",
            "recycling_score": 2,
            "plastic_usage_score": 4,
            "household_size": 3,
            "assessment_period": "monthly"
        }

        response = client.post("/api/v1/assessment/create", json=payload, headers=auth_headers)
        assert response.status_code == 201

        body = response.json()
        assert body["success"] is True
        data = body["data"]
        assert "assessment_id" in data
        assert data["total_emission"] > 0
        assert data["transport"] == 27.0  # 150.0 * 0.18

    def test_create_assessment_unauthorized(self, client: TestClient):
        """POST /create without auth headers returns 401."""
        response = client.post("/api/v1/assessment/create", json={})
        assert response.status_code == 401

    def test_create_assessment_validation_error(self, client: TestClient, auth_headers: dict):
        """POST /create with invalid inputs returns 422."""
        payload = {
            "distance_km": -100.0  # invalid distance
        }
        response = client.post("/api/v1/assessment/create", json=payload, headers=auth_headers)
        assert response.status_code == 422


    # ═══════════════════════════════════════════════════════════════════════════
    # GET /api/v1/assessment/history
    # ═══════════════════════════════════════════════════════════════════════════

    def test_get_history_success(self, client: TestClient, db: Session, test_user, auth_headers: dict):
        """GET /history retrieves past assessments for the logged-in user."""
        # Seed assessments
        res1 = AssessmentService.create_assessment(db, test_user.id, {"diet_type": "mixed"})
        
        # Manually alter created_at of res1 to be older to prevent SQLite timestamp collisions
        a1 = db.query(CarbonAssessment).filter(CarbonAssessment.id == res1["assessment_id"]).first()
        a1.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()

        res2 = AssessmentService.create_assessment(db, test_user.id, {"diet_type": "mixed"})

        response = client.get("/api/v1/assessment/history", headers=auth_headers)
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        assert len(body["data"]) == 2
        assert body["data"][0]["assessment_id"] == str(res2["assessment_id"])
        assert body["data"][1]["assessment_id"] == str(res1["assessment_id"])

    def test_get_history_unauthorized(self, client: TestClient):
        """GET /history without auth headers returns 401."""
        response = client.get("/api/v1/assessment/history")
        assert response.status_code == 401


    # ═══════════════════════════════════════════════════════════════════════════
    # GET /api/v1/assessment/latest
    # ═══════════════════════════════════════════════════════════════════════════

    def test_get_latest_success(self, client: TestClient, db: Session, test_user, auth_headers: dict):
        """GET /latest returns the most recent assessment."""
        res1 = AssessmentService.create_assessment(db, test_user.id, {"diet_type": "mixed"})
        
        # Manually alter created_at of res1 to be older to prevent SQLite timestamp collisions
        a1 = db.query(CarbonAssessment).filter(CarbonAssessment.id == res1["assessment_id"]).first()
        a1.created_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        db.commit()

        latest = AssessmentService.create_assessment(db, test_user.id, {"diet_type": "vegetarian"})

        response = client.get("/api/v1/assessment/latest", headers=auth_headers)
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        assert body["data"]["assessment_id"] == str(latest["assessment_id"])
        assert body["data"]["food"] == 150.0  # vegetarian

    def test_get_latest_not_found(self, client: TestClient, auth_headers: dict):
        """GET /latest returns 404 when there are no assessments."""
        response = client.get("/api/v1/assessment/latest", headers=auth_headers)
        assert response.status_code == 404


    # ═══════════════════════════════════════════════════════════════════════════
    # GET /api/v1/assessment/{assessment_id}
    # ═══════════════════════════════════════════════════════════════════════════

    def test_get_by_id_success(self, client: TestClient, db: Session, test_user, auth_headers: dict):
        """GET /{id} retrieves details of a specific assessment."""
        created = AssessmentService.create_assessment(db, test_user.id, {"diet_type": "mixed"})

        response = client.get(f"/api/v1/assessment/{created['assessment_id']}", headers=auth_headers)
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        assert body["data"]["assessment_id"] == str(created["assessment_id"])

    def test_get_by_id_not_found(self, client: TestClient, auth_headers: dict):
        """GET /{id} returns 404 if not found."""
        random_id = uuid.uuid4()
        response = client.get(f"/api/v1/assessment/{random_id}", headers=auth_headers)
        assert response.status_code == 404

    def test_get_by_id_unauthorized_for_another_user(
        self, client: TestClient, db: Session, test_user, make_user, auth_headers: dict
    ):
        """GET /{id} returns 404 if assessment belongs to another user."""
        other_user = make_user()
        other_assessment = AssessmentService.create_assessment(db, other_user.id, {"diet_type": "mixed"})

        # test_user tries to fetch other_user's assessment
        response = client.get(f"/api/v1/assessment/{other_assessment['assessment_id']}", headers=auth_headers)
        assert response.status_code == 404


    # ═══════════════════════════════════════════════════════════════════════════
    # DELETE /api/v1/assessment/{assessment_id}
    # ═══════════════════════════════════════════════════════════════════════════

    def test_delete_success(self, client: TestClient, db: Session, test_user, auth_headers: dict):
        """DELETE /{id} deletes assessment from DB and returns 204."""
        created = AssessmentService.create_assessment(db, test_user.id, {"diet_type": "mixed"})

        response = client.delete(f"/api/v1/assessment/{created['assessment_id']}", headers=auth_headers)
        assert response.status_code == 204

        # Verify deletion in DB
        assessment = db.query(CarbonAssessment).filter(CarbonAssessment.id == created["assessment_id"]).first()
        assert assessment is None

    def test_delete_unauthorized_for_another_user(
        self, client: TestClient, db: Session, test_user, make_user, auth_headers: dict
    ):
        """DELETE /{id} returns 404 if assessment belongs to another user."""
        other_user = make_user()
        other_assessment = AssessmentService.create_assessment(db, other_user.id, {"diet_type": "mixed"})

        response = client.delete(f"/api/v1/assessment/{other_assessment['assessment_id']}", headers=auth_headers)
        assert response.status_code == 404
