"""
Tests for Dashboard API endpoints (/api/v1/dashboard).

Covers:
- Empty dashboard state (no assessments, goals, streaks, or forecasts)
- Valid summary responses with populated data
- Latest assessment selection and accurate category mapping
- Trend percentage calculation (two assessments, zero previous emissions, insufficient history)
- Total assessment counts
- Active goal filtering and progress inclusion
- Habit streak integration
- Forecast summary integration (available vs missing)
- History endpoint: ordering (descending), response shape, category emissions
- Breakdown endpoint: category breakdown, percentage calculations, safe fallback on empty
- User data isolation (cross-user data cannot leak)
- Unauthenticated access protection (returns 401 / 403)
- Backward compatibility alias routes (/api/v1/dashboard and /api/v1/dashboard/)
"""
import uuid
from datetime import date, datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.models.carbon_assessment import CarbonAssessment
from app.models.forecast import Forecast
from app.models.forecast_point import ForecastPoint
from app.models.goal import Goal
from app.models.habit import Habit
from app.models.enums import AssessmentPeriod, ForecastType, GoalStatus, HabitType
from app.models.user import User


class TestDashboardSummary:

    def test_unauthenticated_access_returns_401(self, client: TestClient):
        """Dashboard endpoints require Bearer auth."""
        res_sum = client.get("/api/v1/dashboard/summary")
        assert res_sum.status_code in (401, 403)

        res_alias = client.get("/api/v1/dashboard")
        assert res_alias.status_code in (401, 403)

        res_hist = client.get("/api/v1/dashboard/history")
        assert res_hist.status_code in (401, 403)

        res_brk = client.get("/api/v1/dashboard/breakdown")
        assert res_brk.status_code in (401, 403)

    def test_empty_dashboard_state(self, client: TestClient, auth_headers: dict):
        """When user has no activity, summary returns sensible zero/null defaults."""
        res = client.get("/api/v1/dashboard/summary", headers=auth_headers)
        assert res.status_code == 200
        payload = res.json()
        assert payload["success"] is True

        data = payload["data"]
        assert data["latest_assessment"] is None
        assert data["trend_delta"] == 0.0
        assert data["trend_percentage"] == 0.0
        assert data["total_assessments"] == 0
        assert data["active_goals_count"] == 0
        assert data["active_goals"] == []
        assert data["current_habit_streak"] == 0
        assert data["forecast_summary"] is None

    def test_compatibility_alias_routes(self, client: TestClient, auth_headers: dict):
        """GET /dashboard and /dashboard/ return the same summary response."""
        res_exact = client.get("/api/v1/dashboard", headers=auth_headers)
        assert res_exact.status_code == 200
        assert res_exact.json()["success"] is True

        res_slash = client.get("/api/v1/dashboard/", headers=auth_headers)
        assert res_slash.status_code == 200
        assert res_slash.json()["success"] is True

        res_summary = client.get("/api/v1/dashboard/summary", headers=auth_headers)
        assert res_summary.status_code == 200
        assert res_exact.json()["data"] == res_summary.json()["data"]

    def test_single_assessment_summary_and_trend(
        self, client: TestClient, db: Session, test_user: User, auth_headers: dict
    ):
        """With 1 assessment, trend is 0.0 and total_assessments is 1."""
        assessment = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=test_user.id,
            transport_emission=120.0,
            energy_emission=180.0,
            food_emission=80.0,
            waste_emission=20.0,
            total_emission=400.0,
            carbon_score=75,
            assessment_period=AssessmentPeriod.monthly,
        )
        db.add(assessment)
        db.commit()

        res = client.get("/api/v1/dashboard/summary", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()["data"]

        assert data["total_assessments"] == 1
        assert data["trend_delta"] == 0.0
        assert data["trend_percentage"] == 0.0
        assert data["latest_assessment"] is not None
        assert data["latest_assessment"]["total_emission"] == 400.0
        assert data["latest_assessment"]["transport_emission"] == 120.0
        assert data["latest_assessment"]["carbon_score"] == 75

    def test_multiple_assessments_trend_calculation(
        self, client: TestClient, db: Session, test_user: User, auth_headers: dict
    ):
        """
        Trend calculates percentage change from previous to latest assessment.
        Previous = 500 kg, Latest = 400 kg -> (400 - 500) / 500 * 100 = -20.0% (reduction).
        """
        now = datetime.now(timezone.utc)
        older = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=test_user.id,
            total_emission=500.0,
            transport_emission=200.0,
            energy_emission=200.0,
            food_emission=80.0,
            waste_emission=20.0,
            created_at=now - timedelta(days=30),
        )
        newer = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=test_user.id,
            total_emission=400.0,
            transport_emission=150.0,
            energy_emission=170.0,
            food_emission=60.0,
            waste_emission=20.0,
            created_at=now,
        )
        db.add_all([older, newer])
        db.commit()

        res = client.get("/api/v1/dashboard/summary", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()["data"]

        assert data["total_assessments"] == 2
        assert data["trend_delta"] == -20.0
        assert data["trend_percentage"] == -20.0
        assert data["latest_assessment"]["total_emission"] == 400.0

    def test_trend_calculation_zero_previous_emission(
        self, client: TestClient, db: Session, test_user: User, auth_headers: dict
    ):
        """Division by zero is guarded when previous assessment has 0.0 total emission."""
        now = datetime.now(timezone.utc)
        older = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=test_user.id,
            total_emission=0.0,
            created_at=now - timedelta(days=10),
        )
        newer = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=test_user.id,
            total_emission=250.0,
            created_at=now,
        )
        db.add_all([older, newer])
        db.commit()

        res = client.get("/api/v1/dashboard/summary", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()["data"]
        assert data["trend_delta"] == 0.0
        assert data["trend_percentage"] == 0.0

    def test_active_goals_and_habit_streak_integration(
        self, client: TestClient, db: Session, test_user: User, auth_headers: dict
    ):
        """Summary aggregates active goals and calculates habit streak correctly."""
        # Active and completed goals
        active_goal = Goal(
            id=uuid.uuid4(),
            user_id=test_user.id,
            goal_name="Reduce car travel",
            target_reduction_percentage=15.0,
            status=GoalStatus.active,
            current_progress=50.0,
        )
        completed_goal = Goal(
            id=uuid.uuid4(),
            user_id=test_user.id,
            goal_name="Switch to LED lights",
            status=GoalStatus.completed,
            current_progress=100.0,
        )
        db.add_all([active_goal, completed_goal])

        # Habit completions on consecutive days (today and yesterday)
        today = date.today()
        h1 = Habit(
            id=uuid.uuid4(),
            user_id=test_user.id,
            habit_type=HabitType.public_transport.value,
            activity_date=today,
            completed=True,
        )
        h2 = Habit(
            id=uuid.uuid4(),
            user_id=test_user.id,
            habit_type=HabitType.save_electricity.value,
            activity_date=today - timedelta(days=1),
            completed=True,
        )
        db.add_all([h1, h2])
        db.commit()

        res = client.get("/api/v1/dashboard/summary", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()["data"]

        assert data["active_goals_count"] == 1
        assert len(data["active_goals"]) == 1
        assert data["active_goals"][0]["goal_name"] == "Reduce car travel"
        assert data["current_habit_streak"] == 2

    def test_forecast_summary_integration(
        self, client: TestClient, db: Session, test_user: User, auth_headers: dict
    ):
        """Summary extracts the 3-month forecast point from the user's latest forecast."""
        fc = Forecast(
            id=uuid.uuid4(),
            user_id=test_user.id,
            forecast_type=ForecastType.recommended_path,
        )
        db.add(fc)
        db.flush()

        pt3 = ForecastPoint(
            id=uuid.uuid4(),
            forecast_id=fc.id,
            month_offset=3,
            predicted_emission=312.45,
        )
        pt6 = ForecastPoint(
            id=uuid.uuid4(),
            forecast_id=fc.id,
            month_offset=6,
            predicted_emission=265.10,
        )
        db.add_all([pt3, pt6])
        db.commit()

        res = client.get("/api/v1/dashboard/summary", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()["data"]

        assert data["forecast_summary"] is not None
        assert data["forecast_summary"]["month_3_emission"] == 312.45


class TestDashboardHistory:

    def test_empty_history(self, client: TestClient, auth_headers: dict):
        """Returns an empty list when user has no assessments."""
        res = client.get("/api/v1/dashboard/history", headers=auth_headers)
        assert res.status_code == 200
        payload = res.json()
        assert payload["success"] is True
        assert payload["data"] == []

    def test_history_ordered_descending(
        self, client: TestClient, db: Session, test_user: User, auth_headers: dict
    ):
        """History returns assessments newest first with category mappings."""
        now = datetime.now(timezone.utc)
        a1 = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=test_user.id,
            total_emission=300.0,
            transport_emission=100.0,
            energy_emission=100.0,
            food_emission=80.0,
            waste_emission=20.0,
            created_at=now - timedelta(days=20),
        )
        a2 = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=test_user.id,
            total_emission=250.0,
            transport_emission=80.0,
            energy_emission=90.0,
            food_emission=60.0,
            waste_emission=20.0,
            created_at=now - timedelta(days=5),
        )
        db.add_all([a1, a2])
        db.commit()

        res = client.get("/api/v1/dashboard/history", headers=auth_headers)
        assert res.status_code == 200
        history = res.json()["data"]

        assert len(history) == 2
        # First item should be the newer one (a2)
        assert history[0]["total_emission"] == 250.0
        assert history[0]["transport"] == 80.0
        assert history[0]["energy"] == 90.0
        assert history[1]["total_emission"] == 300.0


class TestDashboardBreakdown:

    def test_breakdown_with_no_assessment(self, client: TestClient, auth_headers: dict):
        """Gracefully returns 0-values without throwing errors if no assessments exist."""
        res = client.get("/api/v1/dashboard/breakdown", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()["data"]

        assert data["total_emission"] == 0.0
        assert data["categories"]["transport"] == 0.0
        assert data["percentages"]["transport"] == 0.0
        assert data["carbon_score"] is None

    def test_breakdown_with_valid_assessment(
        self, client: TestClient, db: Session, test_user: User, auth_headers: dict
    ):
        """Correctly breaks down category emissions and calculates percentages."""
        assessment = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=test_user.id,
            transport_emission=200.0,
            energy_emission=100.0,
            food_emission=100.0,
            waste_emission=100.0,
            total_emission=500.0,
            carbon_score=80,
        )
        db.add(assessment)
        db.commit()

        res = client.get("/api/v1/dashboard/breakdown", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()["data"]

        assert data["total_emission"] == 500.0
        assert data["transport_emission"] == 200.0
        assert data["categories"]["transport"] == 200.0
        assert data["percentages"]["transport"] == 40.0  # (200 / 500) * 100
        assert data["percentages"]["energy"] == 20.0     # (100 / 500) * 100
        assert data["carbon_score"] == 80


class TestUserDataIsolation:

    def test_dashboard_does_not_leak_other_user_data(
        self, client: TestClient, db: Session, make_user, test_user: User, auth_headers: dict
    ):
        """Data belonging to user B never appears in user A's dashboard."""
        other_user = make_user(email="other_user@example.com")

        # Other user's assessment and goal
        other_assessment = CarbonAssessment(
            id=uuid.uuid4(),
            user_id=other_user.id,
            total_emission=999.0,
            transport_emission=500.0,
            energy_emission=499.0,
        )
        other_goal = Goal(
            id=uuid.uuid4(),
            user_id=other_user.id,
            goal_name="Other user's private goal",
            status=GoalStatus.active,
        )
        db.add_all([other_assessment, other_goal])
        db.commit()

        # Requesting as test_user
        res_sum = client.get("/api/v1/dashboard/summary", headers=auth_headers)
        assert res_sum.status_code == 200
        data_sum = res_sum.json()["data"]
        assert data_sum["total_assessments"] == 0
        assert data_sum["latest_assessment"] is None
        assert data_sum["active_goals_count"] == 0
        assert data_sum["active_goals"] == []

        res_hist = client.get("/api/v1/dashboard/history", headers=auth_headers)
        assert res_hist.status_code == 200
        assert res_hist.json()["data"] == []

        res_brk = client.get("/api/v1/dashboard/breakdown", headers=auth_headers)
        assert res_brk.status_code == 200
        assert res_brk.json()["data"]["total_emission"] == 0.0
