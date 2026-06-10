"""
Simulator router  —  /api/simulator

Endpoints
---------
POST /api/simulator/run              Run a what-if simulation scenario
GET  /api/simulator/                 List saved simulations for the user
GET  /api/simulator/{simulation_id}  Fetch a saved simulation by ID
DELETE /api/simulator/{simulation_id} Delete a simulation

All endpoints return {"detail": "not implemented"} until services are wired.
"""
from fastapi import APIRouter, status
from uuid import UUID

router = APIRouter()

_NOT_IMPLEMENTED = {"detail": "not implemented"}


@router.post(
    "/run",
    status_code=status.HTTP_201_CREATED,
    summary="Run a what-if simulation and persist the scenario result",
)
async def run_simulation():
    return _NOT_IMPLEMENTED


@router.get(
    "/",
    summary="List all saved simulations for the current user",
)
async def list_simulations():
    return _NOT_IMPLEMENTED


@router.get(
    "/{simulation_id}",
    summary="Fetch a specific simulation scenario by ID",
)
async def get_simulation(simulation_id: UUID):
    return _NOT_IMPLEMENTED


@router.delete(
    "/{simulation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved simulation by ID",
)
async def delete_simulation(simulation_id: UUID):
    return _NOT_IMPLEMENTED
