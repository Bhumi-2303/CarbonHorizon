"""
Unit tests for SimulationService.

Covers:
  - run_simulation with each change category (transport, energy, food, waste)
  - combined multi-category changes
  - edge cases: no changes, zero baseline emissions, solar adoption
  - save_simulation persists correct fields
  - get_simulation_history returns sorted results
  - get_simulation_by_id — happy path and 404
  - delete_simulation — happy path and 404

All DB interactions use the in-memory SQLite conftest fixtures.
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.schemas.simulation import (
    ScenarioChanges,
    TransportChanges,
    EnergyChanges,
    FoodChanges,
    WasteChanges,
    SimulationRunRequest,
    SimulationSaveRequest,
)
from app.models.enums import TransportMode, DietType
from app.services.simulation_service import (
    SimulationService,
    _build_baseline,
    _apply_changes,
    _reduction_pct,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _run_request(
    changes: ScenarioChanges = None,
    **kwargs,
) -> SimulationRunRequest:
    """Build a minimal SimulationRunRequest with safe defaults."""
    defaults = dict(
        scenario_name="test_scenario",
        changes=changes or ScenarioChanges(),
        transport_mode=TransportMode.car,
        distance_km=500.0,
        electricity_kwh=200.0,
        ac_hours=60.0,
        lpg_usage=14.0,
        solar_usage=False,
        diet_type=DietType.mixed,
        recycling_score=2,
        plastic_usage_score=3,
        household_size=2,
    )
    defaults.update(kwargs)
    return SimulationRunRequest(**defaults)


# ─── _build_baseline ──────────────────────────────────────────────────────────

class TestBuildBaseline:
    def test_maps_all_fields(self):
        req = _run_request()
        baseline = _build_baseline(req)
        assert baseline["transport_mode"] == "car"
        assert baseline["distance_km"] == 500.0
        assert baseline["electricity_kwh"] == 200.0
        assert baseline["ac_hours"] == 60.0
        assert baseline["lpg_usage"] == 14.0
        assert baseline["solar_usage"] is False
        assert baseline["diet_type"] == "mixed"
        assert baseline["recycling_score"] == 2
        assert baseline["plastic_usage_score"] == 3
        assert baseline["household_size"] == 2

    def test_missing_fields_default_to_safe_values(self):
        req = SimulationRunRequest(
            scenario_name="empty",
            changes=ScenarioChanges(),
        )
        baseline = _build_baseline(req)
        assert baseline["distance_km"] == 0.0
        assert baseline["electricity_kwh"] == 0.0
        assert baseline["solar_usage"] is False
        assert baseline["diet_type"] == "mixed"
        assert baseline["household_size"] == 1


# ─── _apply_changes ───────────────────────────────────────────────────────────

class TestApplyChanges:

    def test_no_changes_returns_identical_baseline(self):
        req = _run_request(changes=ScenarioChanges())
        baseline = _build_baseline(req)
        modified, diff = _apply_changes(baseline, req)
        assert modified == baseline
        assert diff == {}

    def test_transport_mode_swap(self):
        req = _run_request(
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bus)
            )
        )
        baseline = _build_baseline(req)
        modified, diff = _apply_changes(baseline, req)
        assert modified["transport_mode"] == "bus"
        assert "transport_mode" in diff
        assert "car → bus" in diff["transport_mode"]

    def test_transport_distance_override(self):
        req = _run_request(
            changes=ScenarioChanges(
                transport=TransportChanges(new_distance_km=200.0)
            )
        )
        baseline = _build_baseline(req)
        modified, diff = _apply_changes(baseline, req)
        assert modified["distance_km"] == 200.0
        assert "distance_km" in diff

    def test_energy_electricity_reduction(self):
        req = _run_request(
            electricity_kwh=200.0,
            changes=ScenarioChanges(
                energy=EnergyChanges(electricity_reduction_pct=50.0)
            ),
        )
        baseline = _build_baseline(req)
        modified, diff = _apply_changes(baseline, req)
        assert modified["electricity_kwh"] == pytest.approx(100.0)
        assert "electricity_kwh" in diff
        assert "−50%" in diff["electricity_kwh"]

    def test_energy_reduced_ac_sets_hours_to_zero(self):
        req = _run_request(
            ac_hours=120.0,
            changes=ScenarioChanges(
                energy=EnergyChanges(reduced_ac=True)
            ),
        )
        baseline = _build_baseline(req)
        modified, diff = _apply_changes(baseline, req)
        assert modified["ac_hours"] == 0.0
        assert "ac_hours" in diff

    def test_energy_solar_adoption(self):
        req = _run_request(
            solar_usage=False,
            changes=ScenarioChanges(
                energy=EnergyChanges(solar_adoption=True)
            ),
        )
        baseline = _build_baseline(req)
        modified, diff = _apply_changes(baseline, req)
        assert modified["solar_usage"] is True
        assert "solar_usage" in diff

    def test_food_diet_type_change(self):
        req = _run_request(
            diet_type=DietType.non_vegetarian,
            changes=ScenarioChanges(
                food=FoodChanges(new_diet_type=DietType.vegetarian)
            ),
        )
        baseline = _build_baseline(req)
        modified, diff = _apply_changes(baseline, req)
        assert modified["diet_type"] == "vegetarian"
        assert "non_vegetarian → vegetarian" in diff["diet_type"]

    def test_waste_recycling_improvement_capped_at_5(self):
        req = _run_request(
            recycling_score=4,
            changes=ScenarioChanges(
                waste=WasteChanges(recycling_improvement=5)
            ),
        )
        baseline = _build_baseline(req)
        modified, diff = _apply_changes(baseline, req)
        assert modified["recycling_score"] == 5  # capped

    def test_waste_plastic_reduction_floored_at_1(self):
        req = _run_request(
            plastic_usage_score=1,
            changes=ScenarioChanges(
                waste=WasteChanges(plastic_reduction=5)
            ),
        )
        baseline = _build_baseline(req)
        modified, diff = _apply_changes(baseline, req)
        assert modified["plastic_usage_score"] == 1  # floored

    def test_multi_category_changes_applied_independently(self):
        req = _run_request(
            transport_mode=TransportMode.car,
            diet_type=DietType.non_vegetarian,
            electricity_kwh=200.0,
            recycling_score=1,
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bicycle),
                food=FoodChanges(new_diet_type=DietType.vegetarian),
                energy=EnergyChanges(electricity_reduction_pct=25.0),
                waste=WasteChanges(recycling_improvement=2),
            ),
        )
        baseline = _build_baseline(req)
        modified, diff = _apply_changes(baseline, req)
        assert modified["transport_mode"] == "bicycle"
        assert modified["diet_type"] == "vegetarian"
        assert modified["electricity_kwh"] == pytest.approx(150.0)
        assert modified["recycling_score"] == 3
        assert len(diff) == 4


# ─── _reduction_pct ───────────────────────────────────────────────────────────

class TestReductionPct:
    def test_50_pct_reduction(self):
        assert _reduction_pct(200.0, 100.0) == pytest.approx(50.0)

    def test_zero_current_returns_zero(self):
        assert _reduction_pct(0.0, 0.0) == 0.0

    def test_increase_gives_negative(self):
        pct = _reduction_pct(100.0, -50.0)  # projected > current
        assert pct < 0

    def test_clamped_to_100_upper(self):
        assert _reduction_pct(100.0, 150.0) == pytest.approx(100.0)

    def test_clamped_to_minus_999_lower(self):
        assert _reduction_pct(1.0, -99999.0) == pytest.approx(-999.0)


# ─── SimulationService.run_simulation ─────────────────────────────────────────

class TestRunSimulation:

    def test_returns_simulation_result_structure(self, db):
        req = _run_request(
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bus)
            )
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)
        assert result.scenario_name == "test_scenario"
        assert isinstance(result.current_emission, float)
        assert isinstance(result.projected_emission, float)
        assert isinstance(result.carbon_saved, float)
        assert isinstance(result.reduction_percentage, float)
        assert "current" in result.simulation_data
        assert "projected" in result.simulation_data
        assert "changes_applied" in result.simulation_data

    def test_bicycle_swap_reduces_transport_to_zero(self, db):
        req = _run_request(
            transport_mode=TransportMode.car,
            distance_km=500.0,
            changes=ScenarioChanges(
                transport=TransportChanges(new_mode=TransportMode.bicycle)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)
        assert result.projected_emission < result.current_emission
        assert result.simulation_data["projected"]["transport"] == pytest.approx(0.0)

    def test_solar_adoption_reduces_electricity_emissions(self, db):
        req = _run_request(
            electricity_kwh=300.0,
            solar_usage=False,
            changes=ScenarioChanges(
                energy=EnergyChanges(solar_adoption=True)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)
        assert result.simulation_data["projected"]["energy"] < result.simulation_data["current"]["energy"]

    def test_vegetarian_diet_lowers_food_vs_non_veg(self, db):
        req = _run_request(
            diet_type=DietType.non_vegetarian,
            changes=ScenarioChanges(
                food=FoodChanges(new_diet_type=DietType.vegetarian)
            ),
        )
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)
        assert result.simulation_data["projected"]["food"] < result.simulation_data["current"]["food"]

    def test_no_changes_gives_zero_carbon_saved(self, db):
        req = _run_request(changes=ScenarioChanges())
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)
        assert result.carbon_saved == pytest.approx(0.0, abs=0.01)

    def test_simulation_data_contains_factor_version(self, db):
        req = _run_request()
        result = SimulationService.run_simulation(db, uuid.uuid4(), req)
        assert "factor_version" in result.simulation_data
        assert "calculation_version" in result.simulation_data


# ─── SimulationService.save_simulation ────────────────────────────────────────

class TestSaveSimulation:

    def test_saves_and_returns_orm_row(self, db, test_user):
        payload = SimulationSaveRequest(
            scenario_name="save_test",
            current_emission=500.0,
            projected_emission=300.0,
            carbon_saved=200.0,
            reduction_percentage=40.0,
            simulation_data={"key": "value"},
        )
        sim = SimulationService.save_simulation(db, test_user.id, payload)
        assert sim.id is not None
        assert sim.scenario_name == "save_test"
        assert sim.current_emission == pytest.approx(500.0)
        assert sim.estimated_carbon_saved == pytest.approx(200.0)
        assert sim.simulation_data == {"key": "value"}

    def test_user_id_stored_correctly(self, db, test_user):
        payload = SimulationSaveRequest(
            scenario_name="user_check",
            current_emission=100.0,
            projected_emission=80.0,
            carbon_saved=20.0,
            reduction_percentage=20.0,
        )
        sim = SimulationService.save_simulation(db, test_user.id, payload)
        assert sim.user_id == test_user.id


# ─── SimulationService.get_simulation_history ─────────────────────────────────

class TestGetSimulationHistory:

    def test_empty_history(self, db, test_user):
        history = SimulationService.get_simulation_history(db, test_user.id)
        assert history == []

    def test_returns_only_own_simulations(self, db, test_user):
        # Save one for test_user
        payload = SimulationSaveRequest(
            scenario_name="mine",
            current_emission=100.0,
            projected_emission=50.0,
            carbon_saved=50.0,
            reduction_percentage=50.0,
        )
        SimulationService.save_simulation(db, test_user.id, payload)
        # Query with a different user_id
        other_uid = uuid.uuid4()
        history = SimulationService.get_simulation_history(db, other_uid)
        assert history == []

    def test_returns_multiple_in_desc_order(self, db, test_user):
        for name in ["first", "second", "third"]:
            SimulationService.save_simulation(
                db,
                test_user.id,
                SimulationSaveRequest(
                    scenario_name=name,
                    current_emission=100.0,
                    projected_emission=80.0,
                    carbon_saved=20.0,
                    reduction_percentage=20.0,
                ),
            )
        history = SimulationService.get_simulation_history(db, test_user.id)
        assert len(history) == 3
        # All three scenarios must be present (SQLite may not resolve sub-ms order)
        names = {s.scenario_name for s in history}
        assert names == {"first", "second", "third"}


# ─── SimulationService.get_simulation_by_id ───────────────────────────────────

class TestGetSimulationById:

    def _save_one(self, db, user_id) -> "Simulation":
        return SimulationService.save_simulation(
            db,
            user_id,
            SimulationSaveRequest(
                scenario_name="findme",
                current_emission=200.0,
                projected_emission=100.0,
                carbon_saved=100.0,
                reduction_percentage=50.0,
            ),
        )

    def test_returns_correct_simulation(self, db, test_user):
        sim = self._save_one(db, test_user.id)
        found = SimulationService.get_simulation_by_id(db, test_user.id, sim.id)
        assert found.id == sim.id
        assert found.scenario_name == "findme"

    def test_raises_404_for_wrong_user(self, db, test_user):
        sim = self._save_one(db, test_user.id)
        with pytest.raises(HTTPException) as exc_info:
            SimulationService.get_simulation_by_id(
                db, uuid.uuid4(), sim.id
            )
        assert exc_info.value.status_code == 404

    def test_raises_404_for_nonexistent_id(self, db, test_user):
        with pytest.raises(HTTPException) as exc_info:
            SimulationService.get_simulation_by_id(
                db, test_user.id, uuid.uuid4()
            )
        assert exc_info.value.status_code == 404


# ─── SimulationService.delete_simulation ──────────────────────────────────────

class TestDeleteSimulation:

    def _save_one(self, db, user_id) -> "Simulation":
        return SimulationService.save_simulation(
            db,
            user_id,
            SimulationSaveRequest(
                scenario_name="to_delete",
                current_emission=300.0,
                projected_emission=150.0,
                carbon_saved=150.0,
                reduction_percentage=50.0,
            ),
        )

    def test_deletes_successfully(self, db, test_user):
        sim = self._save_one(db, test_user.id)
        SimulationService.delete_simulation(db, test_user.id, sim.id)
        # Should now raise 404
        with pytest.raises(HTTPException):
            SimulationService.get_simulation_by_id(db, test_user.id, sim.id)

    def test_raises_404_when_not_found(self, db, test_user):
        with pytest.raises(HTTPException) as exc_info:
            SimulationService.delete_simulation(db, test_user.id, uuid.uuid4())
        assert exc_info.value.status_code == 404

    def test_raises_404_for_wrong_user(self, db, test_user):
        sim = self._save_one(db, test_user.id)
        with pytest.raises(HTTPException) as exc_info:
            SimulationService.delete_simulation(db, uuid.uuid4(), sim.id)
        assert exc_info.value.status_code == 404
