"""
tests/test_forecast_service.py
================================
Comprehensive tests for forecast_service.py and the
POST /api/v1/forecast/generate endpoint.

Covers
------
Unit (helpers + ForecastService)
  TestComputeForecastPoint
      — formula: current × (1 − rate)^offset
      — zero rate → flat; rate=1.0 → zero; negative clamped to 0
  TestCurrentPathForecast
      — monthly_rate == 0.0 → all points equal current_emission
  TestRecommendedPathForecast
      — no saved simulations → rate = HABIT_IMPACT_RATE (0.20)
      — with best simulation 50% → boost capped at MAX_SIM_BOOST (0.30)
      — combined rate capped at MAX_COMBINED (0.50)
  TestCustomPathForecast
      — weighted-average rate computed from category emissions
      — zero-emission baseline falls back to simple mean
      — partial category rates (others = 0.0)
  TestGenerateForecast (integration: service + DB)
      — returns Forecast ORM with exactly 3 points at offsets [3,6,12]
      — raises 422 when no assessment exists
      — current_path: all predicted_emission == current_emission
      — recommended_path: emissions strictly decrease per offset
      — custom_path: custom rate is applied correctly
      — saves correctly linked user_id
  TestForecastPersistence
      — get_forecast_history returns all rows, newest first
      — get_forecast_by_id: found / 404 for wrong user / 404 for missing id
      — delete_forecast removes row + cascade points; 404 for wrong user

Integration (HTTP via TestClient)
  TestForecastEndpoints
      — POST /generate: 201, valid response envelope, 3 points
      — POST /generate: 422 when no assessment exists
      — POST /generate without auth: 401
      — GET /history: 200, returns list (length = saved count)
      — GET /{id}: 200, embedded points, correct forecast_type
      — GET /{id}: 404 for foreign forecast_id
      — DELETE /{id}: 204, subsequent GET returns 404
"""
from __future__ import annotations

import uuid
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.carbon_assessment import CarbonAssessment
from app.models.enums import ForecastType
from app.models.simulation import Simulation
from app.schemas.forecast import (
    CustomReductionRates,
    ForecastGenerateRequest,
)
from app.services.forecast_service import (
    FORECAST_MONTH_OFFSETS,
    HABIT_IMPACT_RATE,
    MAX_COMBINED_REDUCTION_RATE,
    MAX_SIMULATION_BOOST_RATE,
    ForecastService,
    _compute_forecast_point,
    _custom_rate,
    _recommended_rate,
)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _seed_assessment(
    db: Session,
    user_id: uuid.UUID,
    *,
    total: float = 200.0,
    transport: float = 80.0,
    energy: float = 60.0,
    food: float = 50.0,
    waste: float = 10.0,
) -> CarbonAssessment:
    """Persist a minimal CarbonAssessment and return it."""
    a = CarbonAssessment(
        id=uuid.uuid4(),
        user_id=user_id,
        transport_emission=transport,
        energy_emission=energy,
        food_emission=food,
        waste_emission=waste,
        total_emission=total,
        carbon_score=60,
        calculation_version="1.0.0",
        factor_version="IPCC-2024",
        assessment_period="monthly",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


def _seed_simulation(
    db: Session,
    user_id: uuid.UUID,
    *,
    reduction_pct: float,
) -> Simulation:
    """Persist a minimal Simulation with the given reduction_percentage."""
    s = Simulation(
        id=uuid.uuid4(),
        user_id=user_id,
        scenario_name=f"sim_{reduction_pct}",
        current_emission=200.0,
        projected_emission=200.0 * (1 - reduction_pct / 100),
        reduction_percentage=reduction_pct,
        estimated_carbon_saved=200.0 * reduction_pct / 100,
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


def _make_request(
    forecast_type: ForecastType,
    custom_rates: CustomReductionRates | None = None,
) -> ForecastGenerateRequest:
    return ForecastGenerateRequest(
        forecast_type=forecast_type,
        custom_rates=custom_rates,
    )


# ===========================================================================
# ── UNIT: _compute_forecast_point ───────────────────────────────────────────
# ===========================================================================

class TestComputeForecastPoint:
    """Formula: current × (1 − rate)^offset"""

    def test_zero_rate_returns_current(self):
        assert _compute_forecast_point(200.0, 0.0, 6) == pytest.approx(200.0)

    def test_zero_rate_all_offsets_flat(self):
        for offset in FORECAST_MONTH_OFFSETS:
            assert _compute_forecast_point(300.0, 0.0, offset) == pytest.approx(300.0)

    def test_rate_one_returns_zero(self):
        assert _compute_forecast_point(500.0, 1.0, 3) == pytest.approx(0.0, abs=1e-6)

    def test_negative_result_clamped_to_zero(self):
        # rate > 1 is not allowed by schema, but helper should still clamp
        assert _compute_forecast_point(100.0, 2.0, 1) == pytest.approx(0.0, abs=1e-6)

    def test_compound_decay_at_3_months(self):
        # 200 × 0.8^3 = 200 × 0.512 = 102.4
        assert _compute_forecast_point(200.0, 0.20, 3) == pytest.approx(102.4, rel=1e-4)

    def test_compound_decay_at_6_months(self):
        # 200 × 0.8^6 = 200 × 0.262144 = 52.4288
        assert _compute_forecast_point(200.0, 0.20, 6) == pytest.approx(52.4288, rel=1e-4)

    def test_compound_decay_at_12_months(self):
        # 200 × 0.8^12 = 200 × 0.068719 ≈ 13.7439
        expected = 200.0 * (0.8 ** 12)
        assert _compute_forecast_point(200.0, 0.20, 12) == pytest.approx(expected, rel=1e-4)

    def test_zero_emission_always_zero(self):
        for offset in FORECAST_MONTH_OFFSETS:
            assert _compute_forecast_point(0.0, 0.20, offset) == pytest.approx(0.0)

    def test_monotonically_decreasing_with_offset(self):
        """Larger offset → smaller predicted emission when rate > 0."""
        vals = [_compute_forecast_point(300.0, 0.15, m) for m in FORECAST_MONTH_OFFSETS]
        assert vals[0] > vals[1] > vals[2]


# ===========================================================================
# ── UNIT: _recommended_rate ─────────────────────────────────────────────────
# ===========================================================================

class TestRecommendedRate:

    def test_no_simulations_returns_habit_rate_only(self, db: Session, test_user):
        rate = _recommended_rate(db, test_user.id)
        assert rate == pytest.approx(HABIT_IMPACT_RATE)

    def test_simulation_boost_added_to_habit_rate(self, db: Session, test_user):
        # 10% reduction sim → boost = 0.10
        _seed_simulation(db, test_user.id, reduction_pct=10.0)
        rate = _recommended_rate(db, test_user.id)
        expected = min(HABIT_IMPACT_RATE + 0.10, MAX_COMBINED_REDUCTION_RATE)
        assert rate == pytest.approx(expected, rel=1e-4)

    def test_large_simulation_boost_capped_at_max_sim_boost(self, db: Session, test_user):
        # 80% reduction sim → boost capped at MAX_SIMULATION_BOOST_RATE (0.30)
        _seed_simulation(db, test_user.id, reduction_pct=80.0)
        rate = _recommended_rate(db, test_user.id)
        expected = min(HABIT_IMPACT_RATE + MAX_SIMULATION_BOOST_RATE, MAX_COMBINED_REDUCTION_RATE)
        assert rate == pytest.approx(expected, rel=1e-4)

    def test_combined_rate_never_exceeds_max_combined(self, db: Session, test_user):
        _seed_simulation(db, test_user.id, reduction_pct=99.0)
        rate = _recommended_rate(db, test_user.id)
        assert rate <= MAX_COMBINED_REDUCTION_RATE + 1e-9

    def test_only_positive_reductions_count(self, db: Session, test_user):
        # A simulation with reduction_pct=0 should not be picked as "best"
        _seed_simulation(db, test_user.id, reduction_pct=0.0)
        rate = _recommended_rate(db, test_user.id)
        # With no *positive* simulations, only habit_impact applies
        assert rate == pytest.approx(HABIT_IMPACT_RATE)

    def test_picks_highest_simulation(self, db: Session, test_user):
        _seed_simulation(db, test_user.id, reduction_pct=10.0)
        _seed_simulation(db, test_user.id, reduction_pct=25.0)
        rate = _recommended_rate(db, test_user.id)
        expected = min(HABIT_IMPACT_RATE + 0.25, MAX_COMBINED_REDUCTION_RATE)
        assert rate == pytest.approx(expected, rel=1e-4)


# ===========================================================================
# ── UNIT: _custom_rate ──────────────────────────────────────────────────────
# ===========================================================================

class TestCustomRate:

    def _mock_assessment(
        self, transport=80.0, energy=60.0, food=50.0, waste=10.0
    ) -> CarbonAssessment:
        """Build an in-memory (non-persisted) CarbonAssessment."""
        a = CarbonAssessment(
            transport_emission=transport,
            energy_emission=energy,
            food_emission=food,
            waste_emission=waste,
            total_emission=transport + energy + food + waste,
        )
        return a

    def test_uniform_rates_equal_mean(self):
        """When all categories have the same rate, result = that rate."""
        assessment = self._mock_assessment(80.0, 60.0, 50.0, 10.0)
        rates = CustomReductionRates(transport=0.10, energy=0.10, food=0.10, waste=0.10)
        assert _custom_rate(rates, assessment) == pytest.approx(0.10, rel=1e-4)

    def test_weighted_by_emission_share(self):
        """
        Assessment: transport=200, energy=0, food=0, waste=0  (total=200)
        Rates: transport=0.30, rest=0.0
        Expected rate = 0.30 (transport carries all weight)
        """
        assessment = self._mock_assessment(200.0, 0.0, 0.0, 0.0)
        rates = CustomReductionRates(transport=0.30, energy=0.0, food=0.0, waste=0.0)
        assert _custom_rate(rates, assessment) == pytest.approx(0.30, rel=1e-4)

    def test_zero_emission_baseline_uses_simple_mean(self):
        """If total_emission == 0, fall back to simple arithmetic mean."""
        assessment = self._mock_assessment(0.0, 0.0, 0.0, 0.0)
        rates = CustomReductionRates(transport=0.10, energy=0.20, food=0.30, waste=0.40)
        expected = (0.10 + 0.20 + 0.30 + 0.40) / 4.0
        assert _custom_rate(rates, assessment) == pytest.approx(expected, rel=1e-4)

    def test_partial_rates_only_active_categories_counted(self):
        """
        Assessment: transport=100, energy=100 (rest=0)
        Rates: transport=0.20, energy=0.40, food=0, waste=0
        Expected = (0.20×100 + 0.40×100) / 200 = 60/200 = 0.30
        """
        assessment = self._mock_assessment(100.0, 100.0, 0.0, 0.0)
        rates = CustomReductionRates(transport=0.20, energy=0.40, food=0.0, waste=0.0)
        assert _custom_rate(rates, assessment) == pytest.approx(0.30, rel=1e-4)

    def test_all_zero_rates_returns_zero(self):
        assessment = self._mock_assessment(80.0, 60.0, 50.0, 10.0)
        rates = CustomReductionRates(transport=0.0, energy=0.0, food=0.0, waste=0.0)
        assert _custom_rate(rates, assessment) == pytest.approx(0.0)


# ===========================================================================
# ── UNIT/SERVICE: ForecastService.generate_forecast ─────────────────────────
# ===========================================================================

class TestGenerateForecast:

    def test_raises_422_when_no_assessment_exists(self, db: Session, test_user):
        from fastapi import HTTPException
        req = _make_request(ForecastType.current_path)
        with pytest.raises(HTTPException) as exc_info:
            ForecastService.generate_forecast(db, test_user.id, req)
        assert exc_info.value.status_code == 422

    def test_returns_forecast_with_3_points(self, db: Session, test_user):
        _seed_assessment(db, test_user.id)
        req = _make_request(ForecastType.current_path)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        assert len(forecast.forecast_points) == 3

    def test_forecast_points_have_correct_offsets(self, db: Session, test_user):
        _seed_assessment(db, test_user.id)
        req = _make_request(ForecastType.current_path)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        offsets = sorted(p.month_offset for p in forecast.forecast_points)
        assert offsets == sorted(FORECAST_MONTH_OFFSETS)

    def test_current_path_all_points_equal_current_emission(self, db: Session, test_user):
        """current_path: rate=0.0 → all predicted values == 200.0"""
        _seed_assessment(db, test_user.id, total=200.0)
        req = _make_request(ForecastType.current_path)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        for point in forecast.forecast_points:
            assert point.predicted_emission == pytest.approx(200.0, rel=1e-4)

    def test_recommended_path_emissions_strictly_decrease(self, db: Session, test_user):
        """recommended_path with rate > 0 → later offsets yield lower emissions."""
        _seed_assessment(db, test_user.id, total=300.0)
        req = _make_request(ForecastType.recommended_path)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        # Sort points by month_offset
        points = sorted(forecast.forecast_points, key=lambda p: p.month_offset)
        assert points[0].predicted_emission > points[1].predicted_emission > points[2].predicted_emission

    def test_recommended_path_rate_includes_habit_impact(self, db: Session, test_user):
        """
        With no simulations, rate = HABIT_IMPACT_RATE (0.20).
        At month 3: expected = current × 0.8^3
        """
        _seed_assessment(db, test_user.id, total=200.0)
        req = _make_request(ForecastType.recommended_path)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        point_3 = next(p for p in forecast.forecast_points if p.month_offset == 3)
        expected = _compute_forecast_point(200.0, HABIT_IMPACT_RATE, 3)
        assert point_3.predicted_emission == pytest.approx(expected, rel=1e-4)

    def test_recommended_path_boosted_by_best_simulation(self, db: Session, test_user):
        """Best simulation with 20% reduction → rate = 0.20 + 0.20 = 0.40."""
        _seed_assessment(db, test_user.id, total=200.0)
        _seed_simulation(db, test_user.id, reduction_pct=20.0)
        req = _make_request(ForecastType.recommended_path)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        point_3 = next(p for p in forecast.forecast_points if p.month_offset == 3)
        expected_rate = min(HABIT_IMPACT_RATE + 0.20, MAX_COMBINED_REDUCTION_RATE)
        expected = _compute_forecast_point(200.0, expected_rate, 3)
        assert point_3.predicted_emission == pytest.approx(expected, rel=1e-4)

    def test_custom_path_applies_weighted_rate(self, db: Session, test_user):
        """
        Assessment: transport=200, rest=0  (total=200)
        custom transport=0.10, rest=0.0
        → rate = 0.10, 3m emission = 200 × 0.9^3 ≈ 145.8
        """
        _seed_assessment(db, test_user.id, total=200.0, transport=200.0,
                         energy=0.0, food=0.0, waste=0.0)
        rates = CustomReductionRates(transport=0.10, energy=0.0, food=0.0, waste=0.0)
        req = _make_request(ForecastType.custom_path, custom_rates=rates)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        point_3 = next(p for p in forecast.forecast_points if p.month_offset == 3)
        expected = _compute_forecast_point(200.0, 0.10, 3)
        assert point_3.predicted_emission == pytest.approx(expected, rel=1e-4)

    def test_custom_path_no_rates_equals_current_path(self, db: Session, test_user):
        """custom_rates all-zero → same as current_path (flat line)."""
        _seed_assessment(db, test_user.id, total=150.0)
        rates = CustomReductionRates(transport=0.0, energy=0.0, food=0.0, waste=0.0)
        req = _make_request(ForecastType.custom_path, custom_rates=rates)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        for point in forecast.forecast_points:
            assert point.predicted_emission == pytest.approx(150.0, rel=1e-4)

    def test_forecast_stored_with_correct_user_id(self, db: Session, test_user):
        _seed_assessment(db, test_user.id)
        req = _make_request(ForecastType.current_path)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        assert forecast.user_id == test_user.id

    def test_forecast_stored_with_correct_type(self, db: Session, test_user):
        _seed_assessment(db, test_user.id)
        for ftype in [ForecastType.current_path, ForecastType.recommended_path, ForecastType.custom_path]:
            req = _make_request(ftype)
            forecast = ForecastService.generate_forecast(db, test_user.id, req)
            type_val = forecast.forecast_type if isinstance(forecast.forecast_type, str) else forecast.forecast_type.value
            assert type_val == ftype.value

    def test_forecast_points_linked_to_forecast(self, db: Session, test_user):
        _seed_assessment(db, test_user.id)
        req = _make_request(ForecastType.current_path)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        for point in forecast.forecast_points:
            assert point.forecast_id == forecast.id

    def test_predicted_emissions_are_non_negative(self, db: Session, test_user):
        _seed_assessment(db, test_user.id, total=1.0)  # tiny current emission
        req = _make_request(ForecastType.recommended_path)
        forecast = ForecastService.generate_forecast(db, test_user.id, req)
        for point in forecast.forecast_points:
            assert point.predicted_emission >= 0.0


# ===========================================================================
# ── UNIT/SERVICE: persistence (history, get_by_id, delete) ──────────────────
# ===========================================================================

class TestForecastPersistence:

    def _generate(self, db, user_id, forecast_type=ForecastType.current_path):
        _seed_assessment(db, user_id)
        return ForecastService.generate_forecast(
            db, user_id, _make_request(forecast_type)
        )

    def test_get_forecast_history_empty(self, db: Session, test_user):
        history = ForecastService.get_forecast_history(db, test_user.id)
        assert history == []

    def test_get_forecast_history_returns_all_for_user(self, db: Session, test_user):
        _seed_assessment(db, test_user.id)
        for ftype in [ForecastType.current_path, ForecastType.recommended_path]:
            ForecastService.generate_forecast(db, test_user.id, _make_request(ftype))
        history = ForecastService.get_forecast_history(db, test_user.id)
        assert len(history) == 2

    def test_get_forecast_history_excludes_other_users(self, db: Session, test_user, make_user):
        other = make_user()
        _seed_assessment(db, other.id)
        ForecastService.generate_forecast(db, other.id, _make_request(ForecastType.current_path))
        history = ForecastService.get_forecast_history(db, test_user.id)
        assert history == []

    def test_get_forecast_history_includes_points(self, db: Session, test_user):
        _seed_assessment(db, test_user.id)
        ForecastService.generate_forecast(db, test_user.id, _make_request(ForecastType.current_path))
        history = ForecastService.get_forecast_history(db, test_user.id)
        assert all(len(f.forecast_points) == 3 for f in history)

    def test_get_forecast_by_id_returns_correct_forecast(self, db: Session, test_user):
        forecast = self._generate(db, test_user.id)
        fetched  = ForecastService.get_forecast_by_id(db, test_user.id, forecast.id)
        assert fetched.id == forecast.id

    def test_get_forecast_by_id_wrong_user_raises_404(self, db: Session, test_user):
        from fastapi import HTTPException
        forecast = self._generate(db, test_user.id)
        with pytest.raises(HTTPException) as exc_info:
            ForecastService.get_forecast_by_id(db, uuid.uuid4(), forecast.id)
        assert exc_info.value.status_code == 404

    def test_get_forecast_by_id_missing_raises_404(self, db: Session, test_user):
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            ForecastService.get_forecast_by_id(db, test_user.id, uuid.uuid4())
        assert exc_info.value.status_code == 404

    def test_delete_forecast_removes_row(self, db: Session, test_user):
        from fastapi import HTTPException
        forecast = self._generate(db, test_user.id)
        ForecastService.delete_forecast(db, test_user.id, forecast.id)
        with pytest.raises(HTTPException) as exc_info:
            ForecastService.get_forecast_by_id(db, test_user.id, forecast.id)
        assert exc_info.value.status_code == 404

    def test_delete_forecast_wrong_user_raises_404(self, db: Session, test_user):
        from fastapi import HTTPException
        forecast = self._generate(db, test_user.id)
        with pytest.raises(HTTPException) as exc_info:
            ForecastService.delete_forecast(db, uuid.uuid4(), forecast.id)
        assert exc_info.value.status_code == 404

    def test_delete_forecast_cascades_to_points(self, db: Session, test_user):
        from app.models.forecast_point import ForecastPoint
        forecast = self._generate(db, test_user.id)
        forecast_id = forecast.id
        ForecastService.delete_forecast(db, test_user.id, forecast_id)
        points = db.query(ForecastPoint).filter(ForecastPoint.forecast_id == forecast_id).all()
        assert points == []


# ===========================================================================
# ── INTEGRATION TESTS (HTTP via TestClient) ──────────────────────────────────
# ===========================================================================

_CURRENT_PATH_PAYLOAD  = {"forecast_type": "current_path"}
_RECOMMENDED_PAYLOAD   = {"forecast_type": "recommended_path"}
_CUSTOM_PAYLOAD        = {
    "forecast_type": "custom_path",
    "custom_rates": {"transport": 0.10, "energy": 0.05, "food": 0.0, "waste": 0.0},
}


class TestForecastEndpoints:

    # ── helpers ──

    def _seed_db_assessment(self, db: Session, user_id: uuid.UUID, total: float = 200.0):
        return _seed_assessment(db, user_id, total=total)

    # ── POST /generate ────────────────────────────────────────────────────

    def test_generate_returns_201_with_envelope(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        resp = client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert "data" in body

    def test_generate_returns_3_forecast_points(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        resp = client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()["data"]
        assert len(data["forecast_points"]) == 3

    def test_generate_point_offsets_are_3_6_12(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        resp = client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD, headers=auth_headers)
        offsets = sorted(p["month_offset"] for p in resp.json()["data"]["forecast_points"])
        assert offsets == [3, 6, 12]

    def test_generate_current_path_flat_emission(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        """current_path: all predicted_emission ≈ current_emission (rate=0)."""
        self._seed_db_assessment(db, test_user.id, total=200.0)
        resp = client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD, headers=auth_headers)
        for pt in resp.json()["data"]["forecast_points"]:
            assert pt["predicted_emission"] == pytest.approx(200.0, rel=1e-4)

    def test_generate_recommended_path_decreasing_emission(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        """recommended_path: emissions must strictly decrease at each offset."""
        self._seed_db_assessment(db, test_user.id, total=300.0)
        resp = client.post("/api/v1/forecast/generate", json=_RECOMMENDED_PAYLOAD, headers=auth_headers)
        pts = sorted(resp.json()["data"]["forecast_points"], key=lambda p: p["month_offset"])
        assert pts[0]["predicted_emission"] > pts[1]["predicted_emission"] > pts[2]["predicted_emission"]

    def test_generate_custom_path_returns_200_forecast_type(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        resp = client.post("/api/v1/forecast/generate", json=_CUSTOM_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 201
        assert resp.json()["data"]["forecast_type"] == "custom_path"

    def test_generate_422_when_no_assessment(
        self, client: TestClient, auth_headers: dict
    ):
        """Generating a forecast with no prior assessment must return 422."""
        resp = client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 422

    def test_generate_401_without_auth(self, client: TestClient):
        resp = client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD)
        assert resp.status_code == 401

    def test_generate_422_invalid_forecast_type(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        resp = client.post(
            "/api/v1/forecast/generate",
            json={"forecast_type": "invalid_type"},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    # ── GET /history ──────────────────────────────────────────────────────

    def test_history_empty_returns_200_empty_list(
        self, client: TestClient, auth_headers: dict
    ):
        resp = client.get("/api/v1/forecast/history", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"] == []

    def test_history_returns_saved_forecasts(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD, headers=auth_headers)
        client.post("/api/v1/forecast/generate", json=_RECOMMENDED_PAYLOAD, headers=auth_headers)
        resp = client.get("/api/v1/forecast/history", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()["data"]) == 2

    def test_history_items_have_point_count(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD, headers=auth_headers)
        data = client.get("/api/v1/forecast/history", headers=auth_headers).json()["data"]
        assert all(item["point_count"] == 3 for item in data)

    def test_history_401_without_auth(self, client: TestClient):
        resp = client.get("/api/v1/forecast/history")
        assert resp.status_code == 401

    # ── GET /{forecast_id} ────────────────────────────────────────────────

    def test_get_by_id_returns_200_with_points(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        gen_resp = client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD, headers=auth_headers)
        forecast_id = gen_resp.json()["data"]["id"]

        get_resp = client.get(f"/api/v1/forecast/{forecast_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()["data"]
        assert data["id"] == forecast_id
        assert len(data["forecast_points"]) == 3

    def test_get_by_id_returns_correct_forecast_type(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        gen = client.post("/api/v1/forecast/generate", json=_RECOMMENDED_PAYLOAD, headers=auth_headers)
        fid = gen.json()["data"]["id"]
        resp = client.get(f"/api/v1/forecast/{fid}", headers=auth_headers)
        assert resp.json()["data"]["forecast_type"] == "recommended_path"

    def test_get_by_id_404_for_nonexistent(
        self, client: TestClient, auth_headers: dict
    ):
        resp = client.get(f"/api/v1/forecast/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_get_by_id_401_without_auth(self, client: TestClient):
        resp = client.get(f"/api/v1/forecast/{uuid.uuid4()}")
        assert resp.status_code == 401

    # ── DELETE /{forecast_id} ─────────────────────────────────────────────

    def test_delete_returns_204(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        gen = client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD, headers=auth_headers)
        fid = gen.json()["data"]["id"]
        resp = client.delete(f"/api/v1/forecast/{fid}", headers=auth_headers)
        assert resp.status_code == 204

    def test_delete_then_get_returns_404(
        self, client: TestClient, db: Session, test_user, auth_headers: dict
    ):
        self._seed_db_assessment(db, test_user.id)
        gen = client.post("/api/v1/forecast/generate", json=_CURRENT_PATH_PAYLOAD, headers=auth_headers)
        fid = gen.json()["data"]["id"]
        client.delete(f"/api/v1/forecast/{fid}", headers=auth_headers)
        get_resp = client.get(f"/api/v1/forecast/{fid}", headers=auth_headers)
        assert get_resp.status_code == 404

    def test_delete_404_for_nonexistent(
        self, client: TestClient, auth_headers: dict
    ):
        resp = client.delete(f"/api/v1/forecast/{uuid.uuid4()}", headers=auth_headers)
        assert resp.status_code == 404

    def test_delete_401_without_auth(self, client: TestClient):
        resp = client.delete(f"/api/v1/forecast/{uuid.uuid4()}")
        assert resp.status_code == 401
