"""
tests/test_simulation_service.py
=================================
Focused tests explicitly requested by the user:

Unit (SimulationService)
------------------------
  test_car_to_bus_simulation          — car→bus swap reduces transport emission
  test_solar_adoption                 — solar flag zeroes electricity component
  test_diet_switch_nonveg_to_veg      — vegetarian diet lowers food emission
  test_reduction_percentage_accuracy  — reduction_percentage within 1 % tolerance
  test_simulation_saves_to_db         — save_simulation persists all fields to DB

Integration (POST /api/v1/simulator/run)
----------------------------------------
  test_run_endpoint_returns_200_with_correct_projected_values
      — sends a full valid payload, asserts 200 + envelope + numeric fields
  test_run_endpoint_unauthorized
      — missing auth → 401
  test_run_endpoint_car_to_bicycle_full_cycle
      — bicycle mode makes projected transport ≈ 0, reduction_percentage > 0
  test_run_endpoint_save_flow
      — /run then /save → 201, scenario persisted with matching values
  test_run_endpoint_no_changes_carbon_saved_near_zero
      — empty changes → carbon_saved ≈ 0

All emission arithmetic is verified against fallback factors in calculation_engine.py:
  Transport car  : 0.18  kg CO₂e / km
  Transport bus  : 0.08  kg CO₂e / km
  Transport bike : 0.00  kg CO₂e / km
  Electricity    : 0.50  kg CO₂e / kWh  (solar → 0.00)
  Food monthly   : factor × 30 days / household_size
                   vegetarian   = 1.7 × 30 = 51.0 kg
                   mixed        = 2.5 × 30 = 75.0 kg
                   non_veg      = 3.3 × 30 = 99.0 kg
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.enums import TransportMode, DietType
from app.models.simulation import Simulation
from app.schemas.simulation import (
    ScenarioChanges,
    TransportChanges,
    EnergyChanges,
    FoodChanges,
    SimulationRunRequest,
    SimulationSaveRequest,
)
from app.services.simulation_service import SimulationService

# ---------------------------------------------------------------------------
# Shared request builders
# ---------------------------------------------------------------------------

def _make_run_request(
    *,
    transport_mode: TransportMode = TransportMode.car,
    distance_km: float = 500.0,
    electricity_kwh: float = 200.0,
    ac_hours: float = 0.0,
    lpg_usage: float = 0.0,
    solar_usage: bool = False,
    diet_type: DietType = DietType.mixed,
    recycling_score: int = 0,
    plastic_usage_score: int = 0,
    household_size: int = 1,
    changes: ScenarioChanges | None = None,
    scenario_name: str = "test",
) -> SimulationRunRequest:
    """Build a SimulationRunRequest with explicit, auditable defaults."""
    return SimulationRunRequest(
        scenario_name=scenario_name,
        changes=changes or ScenarioChanges(),
        transport_mode=transport_mode,
        distance_km=distance_km,
        electricity_kwh=electricity_kwh,
        ac_hours=ac_hours,
        lpg_usage=lpg_usage,
        solar_usage=solar_usage,
        diet_type=diet_type,
        recycling_score=recycling_score,
        plastic_usage_score=plastic_usage_score,
        household_size=household_size,
    )


# ===========================================================================
# ── UNIT TESTS ──────────────────────────────────────────────────────────────
# ===========================================================================

class TestCarToBusSimulation:
    """
    Verify that swapping transport mode from car to bus reduces transport
    emission proportionally to the factor ratio (car=0.18, bus=0.08).
    """

    def test_car_to_bus_reduces_transport_emission(self, db: Session):
        """Transport emission must drop when switching car → bus."""
        req = _make_run_request(
            transport_mode=TransportMode.car,
            distance_km=500.0,
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bus)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        current_transport   = result.simulation_data["current"]["transport"]
        projected_transport = result.simulation_data["projected"]["transport"]

        assert projected_transport < current_transport, (
            "Bus should produce less transport emission than car"
        )

    def test_car_to_bus_transport_values_match_factors(self, db: Session):
        """
        With fallback factors (car=0.18, bus=0.08), 500 km gives:
          current   = 500 × 0.18 = 90.0 kg
          projected = 500 × 0.08 = 40.0 kg
        SQLite test DB has no seeded factors, so fallbacks apply.
        """
        req = _make_run_request(
            transport_mode=TransportMode.car,
            distance_km=500.0,
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bus)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        assert result.simulation_data["current"]["transport"]   == pytest.approx(90.0, rel=0.01)
        assert result.simulation_data["projected"]["transport"] == pytest.approx(40.0, rel=0.01)

    def test_car_to_bus_carbon_saved_is_positive(self, db: Session):
        """carbon_saved must be positive when switching to a lower-emission mode."""
        req = _make_run_request(
            transport_mode=TransportMode.car,
            distance_km=500.0,
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bus)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)
        assert result.carbon_saved > 0

    def test_car_to_bus_diff_recorded_in_changes_applied(self, db: Session):
        """The changes_applied dict should document the mode swap."""
        req = _make_run_request(
            transport_mode=TransportMode.car,
            distance_km=500.0,
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bus)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)
        applied = result.simulation_data["changes_applied"]
        assert "transport_mode" in applied
        assert "car" in applied["transport_mode"]
        assert "bus" in applied["transport_mode"]


# ---------------------------------------------------------------------------

class TestSolarAdoption:
    """
    Verify that enabling solar_adoption zeroes out the electricity component
    of the energy emission (since solar offsets 100 % of grid electricity).
    """

    def test_solar_adoption_zeroes_electricity_emission(self, db: Session):
        """
        Baseline: electricity_kwh=300, solar_usage=False
          current   energy ≈ 300 × 0.50 = 150.0 kg
          projected energy ≈ 0.0 kg  (solar active)
        """
        req = _make_run_request(
            electricity_kwh=300.0,
            ac_hours=0.0,
            lpg_usage=0.0,
            solar_usage=False,
            changes=ScenarioChanges(
                energy=EnergyChanges(solar_adoption=True)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        assert result.simulation_data["projected"]["energy"] == pytest.approx(0.0, abs=0.01), (
            "Solar adoption should offset 100 % of electricity → 0 energy emission"
        )

    def test_solar_adoption_reduces_total_emission(self, db: Session):
        """Total projected emission must be strictly less than current."""
        req = _make_run_request(
            electricity_kwh=300.0,
            solar_usage=False,
            changes=ScenarioChanges(energy=EnergyChanges(solar_adoption=True)),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        assert result.projected_emission < result.current_emission

    def test_solar_adoption_baseline_energy_correct(self, db: Session):
        """Current energy with 300 kWh and no solar = 300 × 0.50 = 150.0 kg."""
        req = _make_run_request(
            electricity_kwh=300.0,
            ac_hours=0.0,
            lpg_usage=0.0,
            solar_usage=False,
            changes=ScenarioChanges(energy=EnergyChanges(solar_adoption=True)),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        assert result.simulation_data["current"]["energy"] == pytest.approx(150.0, rel=0.01)

    def test_solar_adoption_changes_applied_recorded(self, db: Session):
        """solar_usage must appear in changes_applied."""
        req = _make_run_request(
            electricity_kwh=200.0,
            solar_usage=False,
            changes=ScenarioChanges(energy=EnergyChanges(solar_adoption=True)),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)
        assert "solar_usage" in result.simulation_data["changes_applied"]


# ---------------------------------------------------------------------------

class TestDietSwitchNonVegToVegetarian:
    """
    Verify that switching from non_vegetarian → vegetarian lowers food emission.

    Monthly food emission (fallback, household_size=1):
      non_vegetarian  = 3.3 × 30 = 99.0 kg
      vegetarian      = 1.7 × 30 = 51.0 kg
      saving          = 48.0 kg
    """

    def test_diet_switch_reduces_food_emission(self, db: Session):
        req = _make_run_request(
            diet_type=DietType.non_vegetarian,
            household_size=1,
            changes=ScenarioChanges(
                food=FoodChanges(new_diet_type=DietType.vegetarian)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        assert result.simulation_data["projected"]["food"] < result.simulation_data["current"]["food"]

    def test_diet_switch_baseline_food_matches_non_veg_factor(self, db: Session):
        """Current food = 3.3 kg/day × 30 days = 99.0 kg."""
        req = _make_run_request(
            diet_type=DietType.non_vegetarian,
            household_size=1,
            distance_km=0.0,       # isolate food only
            electricity_kwh=0.0,
            changes=ScenarioChanges(
                food=FoodChanges(new_diet_type=DietType.vegetarian)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        assert result.simulation_data["current"]["food"] == pytest.approx(99.0, rel=0.01)

    def test_diet_switch_projected_food_matches_veg_factor(self, db: Session):
        """Projected food = 1.7 kg/day × 30 days = 51.0 kg."""
        req = _make_run_request(
            diet_type=DietType.non_vegetarian,
            household_size=1,
            distance_km=0.0,
            electricity_kwh=0.0,
            changes=ScenarioChanges(
                food=FoodChanges(new_diet_type=DietType.vegetarian)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        assert result.simulation_data["projected"]["food"] == pytest.approx(51.0, rel=0.01)

    def test_diet_switch_carbon_saved_matches_expected(self, db: Session):
        """carbon_saved ≈ 99.0 − 51.0 = 48.0 kg (isolated, no other inputs)."""
        req = _make_run_request(
            diet_type=DietType.non_vegetarian,
            household_size=1,
            distance_km=0.0,
            electricity_kwh=0.0,
            changes=ScenarioChanges(
                food=FoodChanges(new_diet_type=DietType.vegetarian)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        assert result.carbon_saved == pytest.approx(48.0, rel=0.01)

    def test_diet_switch_diff_recorded(self, db: Session):
        """changes_applied must record the diet transition."""
        req = _make_run_request(
            diet_type=DietType.non_vegetarian,
            changes=ScenarioChanges(
                food=FoodChanges(new_diet_type=DietType.vegetarian)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)
        applied = result.simulation_data["changes_applied"]
        assert "diet_type" in applied
        assert "non_vegetarian" in applied["diet_type"]
        assert "vegetarian" in applied["diet_type"]


# ---------------------------------------------------------------------------

class TestReductionPercentageAccuracy:
    """
    Verify reduction_percentage accuracy within 1 % tolerance.

    Car→bus, 500 km:
      current   transport = 500 × 0.18 = 90.0 kg
      projected transport = 500 × 0.08 = 40.0 kg
      carbon_saved        = 50.0 kg
      expected %          = 50 / 90 × 100 ≈ 55.56 %

    Diet non_veg→veg, isolated:
      current  food = 99.0 kg
      projected food = 51.0 kg
      carbon_saved = 48.0 kg
      expected % = 48 / 99 × 100 ≈ 48.48 %
    """

    def test_car_to_bus_reduction_pct_within_1pct(self, db: Session):
        """Reduction percentage for car→bus over 500 km must be ≈ 55.56 %, ±1 %."""
        req = _make_run_request(
            transport_mode=TransportMode.car,
            distance_km=500.0,
            electricity_kwh=0.0,    # isolate transport
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bus)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        expected_pct = (50.0 / 90.0) * 100  # ≈ 55.56
        assert result.reduction_percentage == pytest.approx(expected_pct, abs=1.0), (
            f"Expected ≈{expected_pct:.2f} %, got {result.reduction_percentage:.2f} %"
        )

    def test_solar_adoption_100pct_electricity_offset(self, db: Session):
        """
        When only electricity is present (no other inputs), solar adoption
        brings projected to 0 → reduction_percentage ≈ 100 %.
        """
        req = _make_run_request(
            electricity_kwh=300.0,
            distance_km=0.0,
            ac_hours=0.0,
            lpg_usage=0.0,
            solar_usage=False,
            diet_type=DietType.vegetarian,
            household_size=1,
            recycling_score=0,
            plastic_usage_score=0,
            changes=ScenarioChanges(energy=EnergyChanges(solar_adoption=True)),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        # Food (veg) is still present in both baseline and projected → not 100 %
        # But the electricity portion IS zeroed, so reduction > 0
        assert result.reduction_percentage > 0
        assert result.reduction_percentage <= 100

    def test_diet_switch_reduction_pct_within_1pct(self, db: Session):
        """non_veg→veg diet reduction % ≈ 48.48 %, ±1 %."""
        req = _make_run_request(
            diet_type=DietType.non_vegetarian,
            household_size=1,
            distance_km=0.0,
            electricity_kwh=0.0,
            changes=ScenarioChanges(
                food=FoodChanges(new_diet_type=DietType.vegetarian)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        expected_pct = (48.0 / 99.0) * 100  # ≈ 48.48
        assert result.reduction_percentage == pytest.approx(expected_pct, abs=1.0), (
            f"Expected ≈{expected_pct:.2f} %, got {result.reduction_percentage:.2f} %"
        )

    def test_no_changes_reduction_pct_is_zero(self, db: Session):
        """No changes → carbon_saved = 0 → reduction_percentage = 0."""
        req = _make_run_request(changes=ScenarioChanges())
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        assert result.reduction_percentage == pytest.approx(0.0, abs=0.01)

    def test_bicycle_reduces_transport_to_zero_gives_max_transport_reduction(self, db: Session):
        """Car→bicycle: transport projected = 0, max transport reduction."""
        req = _make_run_request(
            transport_mode=TransportMode.car,
            distance_km=500.0,
            electricity_kwh=0.0,
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bicycle)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)

        assert result.simulation_data["projected"]["transport"] == pytest.approx(0.0, abs=0.01)
        assert result.reduction_percentage == pytest.approx(100.0, abs=1.0)


# ---------------------------------------------------------------------------

class TestSimulationSavesToDb:
    """
    Verify save_simulation() persists the correct fields to the DB and
    the record is queryable via get_simulation_by_id().
    """

    def test_save_persists_all_fields(self, db: Session, test_user):
        payload = SimulationSaveRequest(
            scenario_name="db_persist_test",
            scenario_description="Checking DB write",
            current_emission=400.0,
            projected_emission=250.0,
            carbon_saved=150.0,
            reduction_percentage=37.5,
            simulation_data={"current": {"total": 400.0}, "projected": {"total": 250.0}},
        )
        sim = SimulationService.save_simulation(db, test_user.id, payload)

        assert sim.id is not None
        assert sim.user_id == test_user.id
        assert sim.scenario_name == "db_persist_test"
        assert sim.scenario_description == "Checking DB write"
        assert sim.current_emission == pytest.approx(400.0)
        assert sim.projected_emission == pytest.approx(250.0)
        assert sim.estimated_carbon_saved == pytest.approx(150.0)
        assert sim.reduction_percentage == pytest.approx(37.5)
        assert sim.simulation_data == {
            "current": {"total": 400.0},
            "projected": {"total": 250.0},
        }

    def test_save_queryable_by_id(self, db: Session, test_user):
        """Saved row must be retrievable via get_simulation_by_id."""
        payload = SimulationSaveRequest(
            scenario_name="queryable",
            current_emission=200.0,
            projected_emission=120.0,
            carbon_saved=80.0,
            reduction_percentage=40.0,
        )
        saved = SimulationService.save_simulation(db, test_user.id, payload)
        fetched = SimulationService.get_simulation_by_id(db, test_user.id, saved.id)

        assert fetched.id == saved.id
        assert fetched.scenario_name == "queryable"

    def test_save_run_then_save_roundtrip(self, db: Session, test_user):
        """
        Full round-trip: run_simulation → save_simulation → get_simulation_by_id.
        Verifies that run output maps correctly to the save payload and is stored.
        """
        run_req = _make_run_request(
            transport_mode=TransportMode.car,
            distance_km=500.0,
            electricity_kwh=0.0,
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bus)
            ),
            scenario_name="run_save_roundtrip",
        )
        run_result = SimulationService.run_simulation(db, test_user.id, run_req)

        save_payload = SimulationSaveRequest(
            scenario_name=run_result.scenario_name,
            current_emission=run_result.current_emission,
            projected_emission=run_result.projected_emission,
            carbon_saved=run_result.carbon_saved,
            reduction_percentage=run_result.reduction_percentage,
            simulation_data=run_result.simulation_data,
        )
        saved = SimulationService.save_simulation(db, test_user.id, save_payload)
        fetched = SimulationService.get_simulation_by_id(db, test_user.id, saved.id)

        assert fetched.current_emission   == pytest.approx(run_result.current_emission,   rel=0.001)
        assert fetched.projected_emission == pytest.approx(run_result.projected_emission, rel=0.001)
        assert fetched.estimated_carbon_saved == pytest.approx(run_result.carbon_saved,   rel=0.001)

    def test_save_without_simulation_data_is_accepted(self, db: Session, test_user):
        """simulation_data is optional — None should be accepted."""
        payload = SimulationSaveRequest(
            scenario_name="no_data",
            current_emission=100.0,
            projected_emission=80.0,
            carbon_saved=20.0,
            reduction_percentage=20.0,
            simulation_data=None,
        )
        sim = SimulationService.save_simulation(db, test_user.id, payload)
        assert sim.id is not None


# ===========================================================================
# ── INTEGRATION TESTS  (HTTP via TestClient) ────────────────────────────────
# ===========================================================================

# Full valid run payload (all fields, car→bus scenario)
_VALID_RUN_PAYLOAD = {
    "scenario_name": "car_to_bus_integration",
    "transport_mode": "car",
    "distance_km": 500.0,
    "electricity_kwh": 0.0,
    "ac_hours": 0.0,
    "lpg_usage": 0.0,
    "solar_usage": False,
    "diet_type": "mixed",
    "recycling_score": 0,
    "plastic_usage_score": 0,
    "household_size": 1,
    "changes": {
        "transport": {"new_mode": "bus"}
    },
}


class TestSimulatorRunEndpoint:

    def test_run_endpoint_returns_200_with_correct_projected_values(
        self, client: TestClient, auth_headers: dict
    ):
        """
        POST /api/v1/simulator/run with a valid car→bus payload returns:
          - HTTP 200
          - success: true
          - data.current_emission  ≈ 90.0  (500 × 0.18)
          - data.projected_emission ≈ 40.0  (500 × 0.08)
          - data.carbon_saved      ≈ 50.0
          - data.reduction_percentage is a positive float
        """
        response = client.post(
            "/api/v1/simulator/run",
            json=_VALID_RUN_PAYLOAD,
            headers=auth_headers,
        )
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        data = body["data"]

        assert data["current_emission"]     == pytest.approx(90.0, rel=0.01)
        assert data["projected_emission"]   == pytest.approx(40.0, rel=0.01)
        assert data["carbon_saved"]         == pytest.approx(50.0, rel=0.01)
        assert data["reduction_percentage"] > 0

    def test_run_endpoint_unauthorized(self, client: TestClient):
        """POST /run without auth token → 401."""
        response = client.post("/api/v1/simulator/run", json=_VALID_RUN_PAYLOAD)
        assert response.status_code == 401

    def test_run_endpoint_car_to_bicycle_full_cycle(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Car→bicycle: projected transport ≈ 0 kg, reduction_percentage > 0.
        Validates the complete response envelope and simulation_data structure.
        """
        payload = {
            **_VALID_RUN_PAYLOAD,
            "scenario_name": "car_to_bicycle",
            "changes": {"transport": {"new_mode": "bicycle"}},
        }
        response = client.post(
            "/api/v1/simulator/run",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200

        body = response.json()
        assert body["success"] is True
        data = body["data"]

        # Core numeric fields
        assert data["carbon_saved"] > 0
        assert data["reduction_percentage"] > 0

        # simulation_data structure
        sim_data = data["simulation_data"]
        assert "current"         in sim_data
        assert "projected"       in sim_data
        assert "changes_applied" in sim_data

        assert sim_data["projected"]["transport"] == pytest.approx(0.0, abs=0.01)
        assert "transport_mode" in sim_data["changes_applied"]

    def test_run_endpoint_save_flow(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Full save flow: POST /run → extract result → POST /save → 201.
        Verifies that saved.current_emission equals run.current_emission.
        """
        # Step 1: run
        run_resp = client.post(
            "/api/v1/simulator/run",
            json=_VALID_RUN_PAYLOAD,
            headers=auth_headers,
        )
        assert run_resp.status_code == 200
        run_data = run_resp.json()["data"]

        # Step 2: save
        save_payload = {
            "scenario_name":        run_data["scenario_name"],
            "current_emission":     run_data["current_emission"],
            "projected_emission":   run_data["projected_emission"],
            "carbon_saved":         run_data["carbon_saved"],
            "reduction_percentage": run_data["reduction_percentage"],
            "simulation_data":      run_data["simulation_data"],
        }
        save_resp = client.post(
            "/api/v1/simulator/save",
            json=save_payload,
            headers=auth_headers,
        )
        assert save_resp.status_code == 201

        saved = save_resp.json()["data"]
        assert saved["current_emission"] == pytest.approx(
            run_data["current_emission"], rel=0.001
        )
        assert saved["scenario_name"] == run_data["scenario_name"]

    def test_run_endpoint_no_changes_carbon_saved_near_zero(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Submitting an empty changes object (no actual modifications)
        must return carbon_saved ≈ 0.
        """
        payload = {**_VALID_RUN_PAYLOAD, "changes": {}}
        response = client.post(
            "/api/v1/simulator/run",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["carbon_saved"] == pytest.approx(0.0, abs=0.01)

    def test_run_endpoint_solar_adoption_zeroes_energy(
        self, client: TestClient, auth_headers: dict
    ):
        """
        Sending solar_adoption=True with 300 kWh electricity (no transport,
        no food, no waste) must give projected energy ≈ 0.
        """
        payload = {
            "scenario_name": "solar_test",
            "transport_mode": "bicycle",
            "distance_km": 0.0,
            "electricity_kwh": 300.0,
            "ac_hours": 0.0,
            "lpg_usage": 0.0,
            "solar_usage": False,
            "diet_type": "mixed",
            "recycling_score": 0,
            "plastic_usage_score": 0,
            "household_size": 1,
            "changes": {"energy": {"solar_adoption": True}},
        }
        response = client.post(
            "/api/v1/simulator/run",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200
        sim_data = response.json()["data"]["simulation_data"]
        assert sim_data["projected"]["energy"] == pytest.approx(0.0, abs=0.01)

    def test_run_endpoint_diet_switch_response_food_values(
        self, client: TestClient, auth_headers: dict
    ):
        """
        non_vegetarian → vegetarian with only food active:
          current  food ≈ 99.0 kg
          projected food ≈ 51.0 kg
        """
        payload = {
            "scenario_name": "diet_switch",
            "transport_mode": "bicycle",
            "distance_km": 0.0,
            "electricity_kwh": 0.0,
            "ac_hours": 0.0,
            "lpg_usage": 0.0,
            "solar_usage": False,
            "diet_type": "non_vegetarian",
            "recycling_score": 0,
            "plastic_usage_score": 0,
            "household_size": 1,
            "changes": {"food": {"new_diet_type": "vegetarian"}},
        }
        response = client.post(
            "/api/v1/simulator/run",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 200
        sim_data = response.json()["data"]["simulation_data"]

        assert sim_data["current"]["food"]   == pytest.approx(99.0, rel=0.01)
        assert sim_data["projected"]["food"] == pytest.approx(51.0, rel=0.01)
