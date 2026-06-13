"""
Simulator router  —  /api/v1/simulator

Endpoints
---------
POST /api/v1/simulator/run
    Run a what-if scenario and return the projected vs current emissions.
    Does NOT persist automatically — use /save to store results you want to keep.

POST /api/v1/simulator/save
    Persist a simulation result to the simulations table.

GET  /api/v1/simulator/history
    List all saved simulations for the current user (newest first).

GET  /api/v1/simulator/{simulation_id}
    Fetch a specific saved simulation by ID.

DELETE /api/v1/simulator/{simulation_id}
    Delete a saved simulation (ownership-checked).

All responses follow the standard APIResponse envelope:
    {"success": true,  "data": { ... }}
    {"success": false, "error": {"code": "...", "message": "..."}}
"""
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, get_db
from app.models.user import User
from app.schemas.simulation import (
    SimulationRunRequest,
    SimulationSaveRequest,
    SimulationRunAPIResponse,
    SimulationSaveAPIResponse,
    SimulationListAPIResponse,
    SimulationDetailAPIResponse,
)
from app.schemas.auth import APIResponse
from app.services.simulation_service import SimulationService

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /run  — compute a what-if scenario (not persisted)
# ---------------------------------------------------------------------------

@router.post(
    "/run",
    response_model=SimulationRunAPIResponse,
    status_code=status.HTTP_200_OK,
    summary="Run a what-if simulation scenario",
    description=(
        "Applies the requested scenario changes on top of the supplied baseline "
        "inputs and runs the carbon calculation engine on both sets of data. "
        "Returns current vs projected emissions and a per-category breakdown. "
        "The result is NOT automatically saved — call POST /save to persist it."
    ),
)
async def run_simulation(
    payload: SimulationRunRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SimulationRunAPIResponse:
    result = SimulationService.run_simulation(db, current_user.id, payload)
    return APIResponse.ok(result)


# ---------------------------------------------------------------------------
# POST /save  — persist a previously computed simulation result
# ---------------------------------------------------------------------------

@router.post(
    "/save",
    response_model=SimulationSaveAPIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a simulation result to the database",
    description=(
        "Persists a SimulationResult (previously returned by POST /run) to the "
        "simulations table so it can be retrieved later via GET /history."
    ),
)
async def save_simulation(
    payload: SimulationSaveRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SimulationSaveAPIResponse:
    sim = SimulationService.save_simulation(db, current_user.id, payload)
    return APIResponse.ok(sim)


# ---------------------------------------------------------------------------
# GET /history  — list all saved simulations for the current user
# ---------------------------------------------------------------------------

@router.get(
    "/history",
    response_model=SimulationListAPIResponse,
    summary="List all saved simulations for the current user",
)
async def get_simulation_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SimulationListAPIResponse:
    sims = SimulationService.get_simulation_history(db, current_user.id)
    return APIResponse.ok(sims)


# ---------------------------------------------------------------------------
# GET /{simulation_id}  — fetch a specific simulation
# ---------------------------------------------------------------------------

@router.get(
    "/{simulation_id}",
    response_model=SimulationDetailAPIResponse,
    summary="Fetch a specific saved simulation by ID",
)
async def get_simulation(
    simulation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> SimulationDetailAPIResponse:
    sim = SimulationService.get_simulation_by_id(db, current_user.id, simulation_id)
    return APIResponse.ok(sim)


# ---------------------------------------------------------------------------
# DELETE /{simulation_id}  — remove a simulation
# ---------------------------------------------------------------------------

@router.delete(
    "/{simulation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved simulation by ID",
)
async def delete_simulation(
    simulation_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> None:
    SimulationService.delete_simulation(db, current_user.id, simulation_id)
    return None
