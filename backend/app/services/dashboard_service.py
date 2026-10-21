"""
DashboardService — Aggregated metrics, trend calculations, and category breakdowns.

Provides:
- get_summary: Aggregated stats for the user dashboard (latest assessment,
  habit streak, active goals count & list, forecast snapshot, and trend percentage).
- get_history: Chronological assessment history for emission charting.
- get_breakdown: Category-level emission breakdown from the latest assessment.

Trend Calculation Formula:
-------------------------
Trend represents percentage change in total emission from the previous assessment:
    trend_percentage = ((latest_emission - previous_emission) / previous_emission) * 100.0

A negative percentage indicates an emission reduction (improvement).
If fewer than 2 assessments exist, or if previous_emission == 0, trend is 0.0.
"""
from __future__ import annotations

import logging
import uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.carbon_assessment import CarbonAssessment
from app.services.goal_service import GoalService
from app.services.habit_service import HabitService
from app.services.forecast_service import ForecastService

logger = logging.getLogger(__name__)


def _map_assessment_to_dict(assessment: CarbonAssessment) -> Dict[str, Any]:
    """Helper to convert a CarbonAssessment ORM instance into a clean dictionary."""
    return {
        "id": assessment.id,
        "assessment_id": assessment.id,
        "total_emission": float(assessment.total_emission or 0.0),
        "transport_emission": float(assessment.transport_emission or 0.0),
        "transport": float(assessment.transport_emission or 0.0),
        "energy_emission": float(assessment.energy_emission or 0.0),
        "energy": float(assessment.energy_emission or 0.0),
        "food_emission": float(assessment.food_emission or 0.0),
        "food": float(assessment.food_emission or 0.0),
        "waste_emission": float(assessment.waste_emission or 0.0),
        "waste": float(assessment.waste_emission or 0.0),
        "housing_emission": float(assessment.housing_emission or 0.0),
        "water_emission": float(assessment.water_emission or 0.0),
        "digital_emission": float(assessment.digital_emission or 0.0),
        "shopping_emission": float(assessment.shopping_emission or 0.0),
        "offsets_total": float(assessment.offsets_total or 0.0),
        "carbon_score": assessment.carbon_score,
        "assessment_period": assessment.assessment_period,
        "created_at": assessment.created_at,
    }


class DashboardService:

    @staticmethod
    def get_summary(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Aggregate overview metrics for the authenticated user's dashboard.
        """
        # 1. Fetch top 2 assessments for latest data & trend calculation
        assessments = (
            db.query(CarbonAssessment)
            .filter(CarbonAssessment.user_id == user_id)
            .order_by(CarbonAssessment.created_at.desc())
            .limit(2)
            .all()
        )

        total_assessments = (
            db.query(func.count(CarbonAssessment.id))
            .filter(CarbonAssessment.user_id == user_id)
            .scalar()
            or 0
        )

        latest_assessment = None
        trend_delta = 0.0

        if assessments:
            latest_assessment = _map_assessment_to_dict(assessments[0])
            if len(assessments) >= 2:
                latest_total = float(assessments[0].total_emission or 0.0)
                previous_total = float(assessments[1].total_emission or 0.0)
                if previous_total > 0.0:
                    trend_delta = round(((latest_total - previous_total) / previous_total) * 100.0, 2)
                else:
                    trend_delta = 0.0

        # 2. Habit streak
        habit_streak = HabitService.calculate_streak(db, user_id)

        # 3. Active goals
        active_goals_orm = GoalService.get_active_goals(db, user_id)
        active_goals = [
            {
                "id": g.id,
                "goal_name": g.goal_name,
                "goal_description": g.goal_description,
                "target_reduction_percentage": g.target_reduction_percentage,
                "target_emission_value": g.target_emission_value,
                "current_progress": g.current_progress,
                "target_date": g.target_date,
                "status": str(g.status.value if hasattr(g.status, "value") else g.status),
            }
            for g in active_goals_orm
        ]

        # 4. Forecast summary (3-month projected emission if available)
        forecast_summary = None
        forecasts = ForecastService.get_forecast_history(db, user_id)
        if forecasts:
            latest_forecast = forecasts[0]
            # Find month 3 point
            pt3 = next((p for p in latest_forecast.forecast_points if p.month_offset == 3), None)
            if pt3:
                forecast_summary = {
                    "month_3_emission": round(float(pt3.predicted_emission), 2)
                }

        return {
            "latest_assessment": latest_assessment,
            "trend_delta": trend_delta,
            "trend_percentage": trend_delta,
            "total_assessments": total_assessments,
            "active_goals_count": len(active_goals),
            "active_goals": active_goals,
            "current_habit_streak": habit_streak,
            "forecast_summary": forecast_summary,
        }

    @staticmethod
    def get_history(db: Session, user_id: uuid.UUID) -> List[Dict[str, Any]]:
        """
        Fetch chronological assessment history for the user, newest first.
        """
        assessments = (
            db.query(CarbonAssessment)
            .filter(CarbonAssessment.user_id == user_id)
            .order_by(CarbonAssessment.created_at.desc())
            .all()
        )
        return [_map_assessment_to_dict(a) for a in assessments]

    @staticmethod
    def get_breakdown(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
        """
        Fetch emission category breakdown and percentages from the user's latest assessment.
        Returns a zero-safe payload if the user has no assessments.
        """
        latest = (
            db.query(CarbonAssessment)
            .filter(CarbonAssessment.user_id == user_id)
            .order_by(CarbonAssessment.created_at.desc())
            .first()
        )

        if not latest:
            return {
                "total_emission": 0.0,
                "transport_emission": 0.0,
                "energy_emission": 0.0,
                "food_emission": 0.0,
                "waste_emission": 0.0,
                "categories": {
                    "transport": 0.0,
                    "energy": 0.0,
                    "food": 0.0,
                    "waste": 0.0,
                    "housing": 0.0,
                    "water": 0.0,
                    "digital": 0.0,
                    "shopping": 0.0,
                },
                "percentages": {
                    "transport": 0.0,
                    "energy": 0.0,
                    "food": 0.0,
                    "waste": 0.0,
                    "housing": 0.0,
                    "water": 0.0,
                    "digital": 0.0,
                    "shopping": 0.0,
                },
                "carbon_score": None,
                "created_at": None,
            }

        total = float(latest.total_emission or 0.0)
        transport = float(latest.transport_emission or 0.0)
        energy = float(latest.energy_emission or 0.0)
        food = float(latest.food_emission or 0.0)
        waste = float(latest.waste_emission or 0.0)
        housing = float(latest.housing_emission or 0.0)
        water = float(latest.water_emission or 0.0)
        digital = float(latest.digital_emission or 0.0)
        shopping = float(latest.shopping_emission or 0.0)

        def pct(val: float) -> float:
            return round((val / total) * 100.0, 1) if total > 0.0 else 0.0

        return {
            "total_emission": total,
            "transport_emission": transport,
            "energy_emission": energy,
            "food_emission": food,
            "waste_emission": waste,
            "categories": {
                "transport": transport,
                "energy": energy,
                "food": food,
                "waste": waste,
                "housing": housing,
                "water": water,
                "digital": digital,
                "shopping": shopping,
            },
            "percentages": {
                "transport": pct(transport),
                "energy": pct(energy),
                "food": pct(food),
                "waste": pct(waste),
                "housing": pct(housing),
                "water": pct(water),
                "digital": pct(digital),
                "shopping": pct(shopping),
            },
            "carbon_score": latest.carbon_score,
            "created_at": latest.created_at,
        }
