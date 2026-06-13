"""
Simulation Pydantic schemas for Carbon Horizon.

Provides:
  ScenarioChanges      — the "what-if" modifications the user wants to test
  SimulationRunRequest — full POST /simulator/run body
  SimulationResult     — result returned by run_simulation()
  SimulationSaveRequest — POST /simulator/save body (result + optional notes)
  SimulationResponse   — serialised Simulation ORM row for GET responses
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.models.enums import DietType, TransportMode
from app.schemas.auth import APIResponse


# ---------------------------------------------------------------------------
# Scenario change specification (what the user wants to test)
# ---------------------------------------------------------------------------

class TransportChanges(BaseModel):
    """
    Swap the primary transport mode and/or distance.

    Supported swaps (non-exhaustive):
      car        → bus / bicycle / train / motorcycle
      motorcycle → train / bus / bicycle
      any mode   → any other valid TransportMode
    """
    new_mode: Optional[TransportMode] = Field(
        None,
        description="Target transport mode to switch to.",
    )
    new_distance_km: Optional[float] = Field(
        None,
        ge=0,
        description="Override monthly distance (km). If omitted, keep current distance.",
    )


class EnergyChanges(BaseModel):
    """
    Percentage / boolean overrides for energy consumption.

    electricity_reduction_pct : reduce monthly kWh by this % (0–100).
    reduced_ac                : if True, set ac_hours to zero.
    solar_adoption            : if True, enable solar offset (cancels grid electricity).
    """
    electricity_reduction_pct: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Reduce electricity_kwh by this percentage (0–100).",
    )
    reduced_ac: Optional[bool] = Field(
        None,
        description="Set ac_hours to 0 when True.",
    )
    solar_adoption: Optional[bool] = Field(
        None,
        description="Enable solar panels to offset grid electricity.",
    )


class FoodChanges(BaseModel):
    """Switch the user's diet type."""
    new_diet_type: Optional[DietType] = Field(
        None,
        description="Target diet to switch to.",
    )


class WasteChanges(BaseModel):
    """
    Improvement targets for waste habits.

    recycling_improvement  : add this many points to recycling_score  (clamped to 5).
    plastic_reduction      : subtract this many points from plastic_usage_score (floor 1).
    """
    recycling_improvement: Optional[int] = Field(
        None,
        ge=0,
        le=5,
        description="Points to add to current recycling_score.",
    )
    plastic_reduction: Optional[int] = Field(
        None,
        ge=0,
        le=5,
        description="Points to subtract from current plastic_usage_score.",
    )


class ScenarioChanges(BaseModel):
    """
    Aggregated 'what-if' changes for a simulation run.
    Any sub-object that is omitted means "keep current inputs unchanged".
    """
    transport: Optional[TransportChanges] = None
    energy:    Optional[EnergyChanges]    = None
    food:      Optional[FoodChanges]      = None
    waste:     Optional[WasteChanges]     = None


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class SimulationRunRequest(BaseModel):
    """
    POST /api/v1/simulator/run

    The client must provide:
      - scenario_name  : a human-readable label for this what-if
      - changes        : the subset of inputs to modify
      - current_inputs : the baseline emission inputs (copied from the latest
                         assessment or supplied directly by the client).
    """
    scenario_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        examples=["Switch to public transport"],
    )
    scenario_description: Optional[str] = Field(
        None,
        max_length=1000,
        description="Optional free-text description of this scenario.",
    )
    changes: ScenarioChanges = Field(
        ...,
        description="The what-if modifications to apply to current inputs.",
    )
    # Baseline inputs (mirrors AssessmentInputs; all Optional so partial input is ok)
    transport_mode:      Optional[TransportMode] = None
    distance_km:         Optional[float]         = Field(None, ge=0)
    electricity_kwh:     Optional[float]         = Field(None, ge=0)
    ac_hours:            Optional[float]         = Field(None, ge=0)
    lpg_usage:           Optional[float]         = Field(None, ge=0)
    solar_usage:         Optional[bool]          = None
    diet_type:           Optional[DietType]      = None
    recycling_score:     Optional[int]           = Field(None, ge=0, le=5)
    plastic_usage_score: Optional[int]           = Field(None, ge=0, le=5)
    household_size:      Optional[int]           = Field(None, ge=1)


class SimulationSaveRequest(BaseModel):
    """
    POST /api/v1/simulator/save

    Persists a previously computed SimulationResult to the simulations table.
    """
    scenario_name:        str            = Field(..., min_length=1, max_length=255)
    scenario_description: Optional[str] = Field(None, max_length=1000)
    current_emission:     float
    projected_emission:   float
    carbon_saved:         float
    reduction_percentage: float
    simulation_data:      Optional[Dict[str, Any]] = None


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class SimulationResult(BaseModel):
    """
    Returned by POST /simulator/run (and embedded in saved rows).

    Fields
    ------
    scenario_name        : label provided by the user
    current_emission     : total emission from the BASELINE inputs  (kg CO₂e)
    projected_emission   : total emission after applying CHANGES     (kg CO₂e)
    carbon_saved         : current − projected  (positive = improvement)
    reduction_percentage : (carbon_saved / current) × 100
    simulation_data      : full breakdown — current vs projected per category,
                           plus a human-readable diff of what changed
    """
    scenario_name:        str
    current_emission:     float
    projected_emission:   float
    carbon_saved:         float
    reduction_percentage: float
    simulation_data:      Dict[str, Any]


class SimulationResponse(BaseModel):
    """Serialised Simulation ORM row (GET endpoints)."""
    id:                   uuid.UUID
    scenario_name:        str
    scenario_description: Optional[str]
    current_emission:     Optional[float]
    projected_emission:   Optional[float]
    reduction_percentage: Optional[float]
    estimated_carbon_saved: Optional[float]
    simulation_data:      Optional[Dict[str, Any]]
    created_at:           datetime

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Typed APIResponse aliases
# ---------------------------------------------------------------------------

SimulationRunAPIResponse    = APIResponse[SimulationResult]
SimulationSaveAPIResponse   = APIResponse[SimulationResponse]
SimulationListAPIResponse   = APIResponse[List[SimulationResponse]]
SimulationDetailAPIResponse = APIResponse[SimulationResponse]
