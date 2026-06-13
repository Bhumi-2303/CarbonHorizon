"""
ForecastService — rule-based emission forecast engine.

Public interface
----------------
ForecastService.generate_forecast(db, user_id, request)
    → Fetch the user's latest assessment, pick the appropriate monthly
      reduction rates for the requested forecast_type, generate forecast
      points at month_offsets [3, 6, 12], persist a Forecast + ForecastPoint
      rows, return the full Forecast ORM object (with points eager-loaded).

ForecastService.get_forecast_history(db, user_id)
    → Return all Forecast rows for the user (newest first).

ForecastService.get_forecast_by_id(db, user_id, forecast_id)
    → Return a single Forecast (ownership-checked). Raises HTTP 404.

ForecastService.delete_forecast(db, user_id, forecast_id)
    → Delete a Forecast and all cascade-deleted ForecastPoints. Raises HTTP 404.

Forecast model design (rule-based)
-----------------------------------
All three paths share the compound-decay formula:

    projected_emission(month) =
        current_emission × (1 − monthly_reduction_rate) ^ month_offset

where monthly_reduction_rate is derived per forecast_type as follows:

current_path
    monthly_reduction_rate = 0.0  →  flat projection (no change)
    Represents "business as usual" — useful as a pessimistic reference.

recommended_path
    monthly_reduction_rate = habit_impact + best_simulation_boost
    habit_impact            = 0.20  (20 % improvement from adopting good habits)
    best_simulation_boost   = min(abs(best_saved_pct) / 100, 0.30)
      where best_saved_pct is the highest reduction_percentage across ALL
      saved simulations for the user (capped at 30 % to stay realistic).
    If no saved simulations exist, best_simulation_boost = 0.0.
    Combined rate is clamped to [0, 0.50].

custom_path
    monthly_reduction_rate = weighted average of per-category rates supplied
      in the request (transport, energy, food, waste).
    Weight is proportional to each category's share of current total emission.
    If all weights are zero (current_emission = 0), use simple mean.

Month offsets generated: 3, 6, 12.

Design notes
------------
* Service is stateless — all methods are @staticmethod.
* Reads the latest CarbonAssessment to obtain current_emission.
  Raises HTTP 422 if no assessment exists.
* Uses eager join-load for forecast_points so callers get a fully populated
  Forecast without a second round-trip.
"""
from __future__ import annotations

import logging
import uuid
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.models.carbon_assessment import CarbonAssessment
from app.models.enums import ForecastType
from app.models.forecast import Forecast
from app.models.forecast_point import ForecastPoint
from app.models.simulation import Simulation
from app.schemas.forecast import ForecastGenerateRequest, CustomReductionRates

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Month horizons to materialise into forecast_points
FORECAST_MONTH_OFFSETS: List[int] = [3, 6, 12]

# Recommended-path constants
HABIT_IMPACT_RATE:          float = 0.20   # 20 % monthly improvement from habits
MAX_SIMULATION_BOOST_RATE:  float = 0.30   # cap on simulation-derived boost
MAX_COMBINED_REDUCTION_RATE: float = 0.50  # absolute ceiling for recommended_path


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_latest_assessment(db: Session, user_id: uuid.UUID) -> CarbonAssessment:
    """
    Retrieve the most recent CarbonAssessment for the user.
    Raises HTTP 422 if no assessments exist.
    """
    assessment = (
        db.query(CarbonAssessment)
        .filter(CarbonAssessment.user_id == user_id)
        .order_by(CarbonAssessment.created_at.desc())
        .first()
    )
    if assessment is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "No carbon assessment found for this user. "
                "Please complete an assessment before generating a forecast."
            ),
        )
    return assessment


def _best_simulation_reduction(db: Session, user_id: uuid.UUID) -> float:
    """
    Return the highest reduction_percentage (as a fraction 0–MAX_SIM_BOOST)
    across all saved simulations for the user.

    If no simulations exist, returns 0.0.
    The value is capped at MAX_SIMULATION_BOOST_RATE.
    """
    best: Optional[Simulation] = (
        db.query(Simulation)
        .filter(
            Simulation.user_id == user_id,
            Simulation.reduction_percentage.isnot(None),
            Simulation.reduction_percentage > 0,
        )
        .order_by(Simulation.reduction_percentage.desc())
        .first()
    )
    if best is None or best.reduction_percentage is None:
        return 0.0

    rate = best.reduction_percentage / 100.0
    return min(rate, MAX_SIMULATION_BOOST_RATE)


def _recommended_rate(db: Session, user_id: uuid.UUID) -> float:
    """
    Compute recommended_path monthly_reduction_rate:
      min(habit_impact + best_simulation_boost, MAX_COMBINED)
    """
    sim_boost = _best_simulation_reduction(db, user_id)
    combined  = HABIT_IMPACT_RATE + sim_boost
    return min(combined, MAX_COMBINED_REDUCTION_RATE)


def _custom_rate(
    rates: CustomReductionRates,
    assessment: CarbonAssessment,
) -> float:
    """
    Compute custom_path monthly_reduction_rate as a weighted average of the
    per-category rates, weighted by each category's share of the total emission.

    Falls back to a simple mean if total_emission is zero or None.
    """
    transport_e = assessment.transport_emission or 0.0
    energy_e    = assessment.energy_emission    or 0.0
    food_e      = assessment.food_emission      or 0.0
    waste_e     = assessment.waste_emission     or 0.0
    total       = transport_e + energy_e + food_e + waste_e

    if total <= 0:
        # No baseline — return simple arithmetic mean
        return (rates.transport + rates.energy + rates.food + rates.waste) / 4.0

    weighted = (
        rates.transport * transport_e
        + rates.energy  * energy_e
        + rates.food    * food_e
        + rates.waste   * waste_e
    )
    return weighted / total


def _compute_forecast_point(
    current_emission: float,
    monthly_rate: float,
    month_offset: int,
) -> float:
    """
    Apply the compound-decay formula:
      projected = current × (1 − rate)^offset

    Result is clamped to ≥ 0.
    """
    projected = current_emission * ((1.0 - monthly_rate) ** month_offset)
    return round(max(0.0, projected), 4)


def _select_monthly_rate(
    request: ForecastGenerateRequest,
    assessment: CarbonAssessment,
    db: Session,
    user_id: uuid.UUID,
) -> float:
    """Dispatch to the correct rate-computation strategy."""
    if request.forecast_type == ForecastType.current_path:
        return 0.0

    if request.forecast_type == ForecastType.recommended_path:
        return _recommended_rate(db, user_id)

    # custom_path
    custom_rates = request.custom_rates or CustomReductionRates()
    return _custom_rate(custom_rates, assessment)


def _load_forecast(db: Session, forecast_id: uuid.UUID) -> Forecast:
    """
    Load a Forecast with its points eagerly joined.
    Returns None if not found.
    """
    return (
        db.query(Forecast)
        .options(joinedload(Forecast.forecast_points))
        .filter(Forecast.id == forecast_id)
        .first()
    )


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class ForecastService:

    @staticmethod
    def generate_forecast(
        db: Session,
        user_id: uuid.UUID,
        request: ForecastGenerateRequest,
    ) -> Forecast:
        """
        Generate and persist a forecast for the user.

        Steps
        -----
        1. Fetch the user's latest CarbonAssessment (422 if none).
        2. Determine the monthly_reduction_rate for the requested forecast_type.
        3. Compute predicted_emission for each month in FORECAST_MONTH_OFFSETS.
        4. Persist a Forecast header row + one ForecastPoint per offset.
        5. Refresh and return the fully loaded Forecast ORM object.
        """
        assessment     = _fetch_latest_assessment(db, user_id)
        current_emission = float(assessment.total_emission or 0.0)
        monthly_rate   = _select_monthly_rate(request, assessment, db, user_id)

        logger.info(
            "Generating forecast: user_id=%s type=%s current_emission=%.2f rate=%.4f",
            user_id, request.forecast_type, current_emission, monthly_rate,
        )

        # ── Create header row ────────────────────────────────────────────────
        forecast = Forecast(
            id=uuid.uuid4(),
            user_id=user_id,
            forecast_type=request.forecast_type,
        )
        db.add(forecast)
        db.flush()  # populate forecast.id before FK insertion

        # ── Create detail rows ───────────────────────────────────────────────
        for offset in FORECAST_MONTH_OFFSETS:
            predicted = _compute_forecast_point(current_emission, monthly_rate, offset)
            point = ForecastPoint(
                id=uuid.uuid4(),
                forecast_id=forecast.id,
                month_offset=offset,
                predicted_emission=predicted,
            )
            db.add(point)

        db.commit()

        # Reload with points eagerly loaded for immediate use by the caller
        loaded = _load_forecast(db, forecast.id)
        logger.info(
            "Forecast saved: id=%s points=%d", forecast.id, len(loaded.forecast_points)
        )
        return loaded

    @staticmethod
    def get_forecast_history(
        db: Session,
        user_id: uuid.UUID,
    ) -> list[Forecast]:
        """
        Return all Forecast rows for the user, newest first.
        Each row has forecast_points eagerly loaded.
        """
        return (
            db.query(Forecast)
            .options(joinedload(Forecast.forecast_points))
            .filter(Forecast.user_id == user_id)
            .order_by(Forecast.created_at.desc())
            .all()
        )

    @staticmethod
    def get_forecast_by_id(
        db: Session,
        user_id: uuid.UUID,
        forecast_id: uuid.UUID,
    ) -> Forecast:
        """
        Fetch a single Forecast (ownership-checked), with points eagerly loaded.
        Raises HTTP 404 if not found or owned by another user.
        """
        forecast = (
            db.query(Forecast)
            .options(joinedload(Forecast.forecast_points))
            .filter(
                Forecast.user_id == user_id,
                Forecast.id      == forecast_id,
            )
            .first()
        )
        if forecast is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Forecast not found",
            )
        return forecast

    @staticmethod
    def delete_forecast(
        db: Session,
        user_id: uuid.UUID,
        forecast_id: uuid.UUID,
    ) -> None:
        """
        Delete a Forecast and all its cascade-deleted ForecastPoints.
        Raises HTTP 404 if not found or owned by another user.
        """
        forecast = (
            db.query(Forecast)
            .filter(
                Forecast.user_id == user_id,
                Forecast.id      == forecast_id,
            )
            .first()
        )
        if forecast is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Forecast not found",
            )
        db.delete(forecast)
        db.commit()
        logger.info("Forecast deleted: id=%s user_id=%s", forecast_id, user_id)
