"""
SimulationService — what-if scenario calculation and persistence.

Public interface
----------------
SimulationService.run_simulation(db, user_id, request)
    → Apply ScenarioChanges on top of baseline inputs, call calculation_engine
      twice (baseline + modified), return SimulationResult.

SimulationService.save_simulation(db, user_id, payload)
    → Persist a SimulationResult to the simulations table.

SimulationService.get_simulation_history(db, user_id)
    → Return all simulations for the user, newest first.

SimulationService.get_simulation_by_id(db, user_id, simulation_id)
    → Return a single simulation (ownership-checked).

SimulationService.delete_simulation(db, user_id, simulation_id)
    → Delete a simulation (ownership-checked).

Design notes
------------
* The service is stateless — every method is a @staticmethod.
* Baseline inputs are whatever the caller provides (could come from the
  latest assessment, or be supplied directly by the client).
* Missing baseline fields default to 0 / False / "mixed" so the engine
  always receives a complete dict.
* Each ScenarioChange sub-object is applied independently and additively;
  order: transport → energy → food → waste.
* carbon_saved = current − projected (positive value = improvement).
* reduction_percentage = (carbon_saved / current) × 100, clamped to [−999, 100].
"""
from __future__ import annotations

import uuid
import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.simulation import Simulation
from app.models.carbon_assessment import CarbonAssessment
from app.models.emission_inputs import EmissionInputs
from app.models.enums import TransportMode, DietType
from app.services import calculation_engine
from app.schemas.simulation import (
    SimulationRunRequest,
    SimulationSaveRequest,
    SimulationResult,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _coerce_transport_mode(val: Optional[Any]) -> Optional[str]:
    """Normalise a TransportMode enum or raw string to a plain string."""
    if val is None:
        return None
    if isinstance(val, TransportMode):
        return val.value
    return str(val)


def _coerce_diet_type(val: Optional[Any]) -> Optional[str]:
    """Normalise a DietType enum or raw string to a plain string."""
    if val is None:
        return None
    if isinstance(val, DietType):
        return val.value
    return str(val)


def _build_baseline(request: SimulationRunRequest) -> Dict[str, Any]:
    """
    Construct the baseline input dict from the request fields.
    Absent fields fall back to safe zero-emission defaults so the engine
    never raises a TypeError on missing keys.
    """
    return {
        "transport_mode":      _coerce_transport_mode(request.transport_mode),
        "distance_km":         request.distance_km         or 0.0,
        "electricity_kwh":     request.electricity_kwh     or 0.0,
        "ac_hours":            request.ac_hours             or 0.0,
        "lpg_usage":           request.lpg_usage            or 0.0,
        "solar_usage":         request.solar_usage          or False,
        "diet_type":           _coerce_diet_type(request.diet_type) or "mixed",
        "recycling_score":     request.recycling_score      or 0,
        "plastic_usage_score": request.plastic_usage_score  or 0,
        "household_size":      request.household_size       or 1,
        "assessment_period":   "monthly",
    }


def _apply_changes(
    baseline: Dict[str, Any],
    request: SimulationRunRequest,
) -> tuple[Dict[str, Any], Dict[str, str]]:
    """
    Apply the ScenarioChanges onto a copy of the baseline dict.

    Returns
    -------
    modified : dict  — the updated inputs to feed into the calculation engine
    diff     : dict  — human-readable description of what changed
    """
    modified = dict(baseline)
    diff: Dict[str, str] = {}

    changes = request.changes

    # ── Transport ─────────────────────────────────────────────────────────
    if changes.transport:
        tc = changes.transport
        if tc.new_mode is not None:
            old_mode = modified.get("transport_mode", "—")
            new_mode = _coerce_transport_mode(tc.new_mode)
            modified["transport_mode"] = new_mode
            diff["transport_mode"] = f"{old_mode} → {new_mode}"

        if tc.new_distance_km is not None:
            old_km = modified.get("distance_km", 0)
            modified["distance_km"] = tc.new_distance_km
            diff["distance_km"] = f"{old_km} km → {tc.new_distance_km} km"

    # ── Energy ────────────────────────────────────────────────────────────
    if changes.energy:
        ec = changes.energy

        if ec.electricity_reduction_pct is not None:
            old_kwh = modified.get("electricity_kwh", 0.0)
            reduction = old_kwh * (ec.electricity_reduction_pct / 100.0)
            new_kwh = max(0.0, old_kwh - reduction)
            modified["electricity_kwh"] = new_kwh
            diff["electricity_kwh"] = (
                f"{old_kwh:.1f} kWh → {new_kwh:.1f} kWh "
                f"(−{ec.electricity_reduction_pct:.0f}%)"
            )

        if ec.reduced_ac:
            old_ac = modified.get("ac_hours", 0.0)
            modified["ac_hours"] = 0.0
            diff["ac_hours"] = f"{old_ac:.1f} hrs → 0 hrs (AC eliminated)"

        if ec.solar_adoption is not None:
            modified["solar_usage"] = ec.solar_adoption
            diff["solar_usage"] = (
                "enabled (100% grid offset)" if ec.solar_adoption else "disabled"
            )

    # ── Food ──────────────────────────────────────────────────────────────
    if changes.food:
        fc = changes.food
        if fc.new_diet_type is not None:
            old_diet = modified.get("diet_type", "—")
            new_diet = _coerce_diet_type(fc.new_diet_type)
            modified["diet_type"] = new_diet
            diff["diet_type"] = f"{old_diet} → {new_diet}"

    # ── Waste ─────────────────────────────────────────────────────────────
    if changes.waste:
        wc = changes.waste

        if wc.recycling_improvement is not None:
            old_r = modified.get("recycling_score", 0)
            new_r = min(5, old_r + wc.recycling_improvement)
            modified["recycling_score"] = new_r
            diff["recycling_score"] = f"{old_r} → {new_r} (+{wc.recycling_improvement})"

        if wc.plastic_reduction is not None:
            old_p = modified.get("plastic_usage_score", 0)
            new_p = max(1, old_p - wc.plastic_reduction)
            modified["plastic_usage_score"] = new_p
            diff["plastic_usage_score"] = f"{old_p} → {new_p} (−{wc.plastic_reduction})"

    return modified, diff


def _reduction_pct(current: float, saved: float) -> float:
    """Return reduction % clamped to [−999, 100]; 0 if current == 0."""
    if current == 0:
        return 0.0
    raw = (saved / current) * 100.0
    return max(-999.0, min(100.0, raw))


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class SimulationService:

    @staticmethod
    def run_simulation(
        db: Session,
        user_id: uuid.UUID,
        request: SimulationRunRequest,
    ) -> SimulationResult:
        """
        Run a what-if simulation.

        1. Build baseline inputs from the request fields.
        2. Apply ScenarioChanges to produce a modified input dict.
        3. Run the calculation engine on BOTH sets of inputs.
        4. Compute carbon_saved and reduction_percentage.
        5. Return a structured SimulationResult (not yet persisted).
        """
        baseline = _build_baseline(request)
        modified, diff = _apply_changes(baseline, request)

        # Engine calls — pass db so live carbon factors are used
        baseline_result = calculation_engine.calculate_total_emissions(db, baseline)
        modified_result = calculation_engine.calculate_total_emissions(db, modified)

        current_emission   = float(baseline_result["total_emission"])
        projected_emission = float(modified_result["total_emission"])
        carbon_saved       = round(current_emission - projected_emission, 4)
        reduction_pct      = _reduction_pct(current_emission, carbon_saved)

        simulation_data: Dict[str, Any] = {
            # Per-category comparison
            "current": {
                "transport": baseline_result["transport_emission"],
                "energy":    baseline_result["energy_emission"],
                "food":      baseline_result["food_emission"],
                "waste":     baseline_result["waste_emission"],
                "total":     current_emission,
                "score":     baseline_result["carbon_score"],
            },
            "projected": {
                "transport": modified_result["transport_emission"],
                "energy":    modified_result["energy_emission"],
                "food":      modified_result["food_emission"],
                "waste":     modified_result["waste_emission"],
                "total":     projected_emission,
                "score":     modified_result["carbon_score"],
            },
            # What changed
            "changes_applied": diff,
            # Versioning
            "calculation_version": baseline_result["calculation_version"],
            "factor_version":      baseline_result["factor_version"],
        }

        return SimulationResult(
            scenario_name=request.scenario_name,
            current_emission=current_emission,
            projected_emission=projected_emission,
            carbon_saved=carbon_saved,
            reduction_percentage=round(reduction_pct, 2),
            simulation_data=simulation_data,
        )

    @staticmethod
    def save_simulation(
        db: Session,
        user_id: uuid.UUID,
        payload: SimulationSaveRequest,
    ) -> Simulation:
        """
        Persist a SimulationResult to the simulations table.
        Returns the newly created Simulation ORM instance.
        """
        sim = Simulation(
            id=uuid.uuid4(),
            user_id=user_id,
            scenario_name=payload.scenario_name,
            scenario_description=payload.scenario_description,
            current_emission=payload.current_emission,
            projected_emission=payload.projected_emission,
            reduction_percentage=payload.reduction_percentage,
            estimated_carbon_saved=payload.carbon_saved,
            simulation_data=payload.simulation_data,
        )
        db.add(sim)
        db.commit()
        db.refresh(sim)
        logger.info(
            "Simulation saved: id=%s user_id=%s scenario=%r",
            sim.id, user_id, sim.scenario_name,
        )
        return sim

    @staticmethod
    def get_simulation_history(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[Simulation]:
        """
        Return all simulations for the user, newest first.
        """
        return (
            db.query(Simulation)
            .filter(Simulation.user_id == user_id)
            .order_by(Simulation.created_at.desc())
            .all()
        )

    @staticmethod
    def get_simulation_by_id(
        db: Session,
        user_id: uuid.UUID,
        simulation_id: uuid.UUID,
    ) -> Simulation:
        """
        Fetch a single simulation, verifying ownership.
        Raises HTTP 404 if not found or owned by another user.
        """
        sim = (
            db.query(Simulation)
            .filter(
                Simulation.user_id == user_id,
                Simulation.id == simulation_id,
            )
            .first()
        )
        if sim is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation not found",
            )
        return sim

    @staticmethod
    def delete_simulation(
        db: Session,
        user_id: uuid.UUID,
        simulation_id: uuid.UUID,
    ) -> None:
        """
        Delete a simulation, verifying ownership.
        Raises HTTP 404 if not found or owned by another user.
        """
        sim = (
            db.query(Simulation)
            .filter(
                Simulation.user_id == user_id,
                Simulation.id == simulation_id,
            )
            .first()
        )
        if sim is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Simulation not found",
            )
        db.delete(sim)
        db.commit()
        logger.info(
            "Simulation deleted: id=%s user_id=%s", simulation_id, user_id
        )
