import uuid
from typing import Any
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models.carbon_assessment import CarbonAssessment
from app.models.goal import Goal
from app.models.habit import Habit
from app.models.enums import GoalStatus, UserLevel

class ProgressionService:
    @staticmethod
    def calculate_progression(db: Session, user_id: uuid.UUID) -> dict[str, Any]:
        # Count assessments
        assessments_count = db.execute(
            select(func.count(CarbonAssessment.id))
            .where(CarbonAssessment.user_id == user_id)
        ).scalar() or 0

        # Count completed goals
        goals_completed = db.execute(
            select(func.count(Goal.id))
            .where(Goal.user_id == user_id, Goal.status == GoalStatus.completed)
        ).scalar() or 0

        # Count logged habits (any completed habit)
        habits_logged = db.execute(
            select(func.count(Habit.id))
            .where(Habit.user_id == user_id, Habit.completed == True)
        ).scalar() or 0

        # Calculate emission reduction
        # Need oldest and newest assessment
        assessments = db.execute(
            select(CarbonAssessment.total_emission)
            .where(CarbonAssessment.user_id == user_id)
            .order_by(CarbonAssessment.created_at.asc())
        ).scalars().all()

        emission_reduction_tons = 0.0
        if len(assessments) >= 2:
            first_emission = assessments[0]
            latest_emission = assessments[-1]
            if first_emission > latest_emission:
                emission_reduction_tons = first_emission - latest_emission

        # Calculate points
        points = (assessments_count * 100) + (goals_completed * 50) + (habits_logged * 10) + int(emission_reduction_tons * 50)

        # Determine level and next level points
        level = UserLevel.seedling
        next_level_points = 200
        progress_percentage = 0

        if points >= 2001:
            level = UserLevel.planet_protector
            next_level_points = points  # Max level
            progress_percentage = 100
        elif points >= 1001:
            level = UserLevel.climate_champion
            next_level_points = 2001
            progress_percentage = int(((points - 1001) / 1000) * 100)
        elif points >= 501:
            level = UserLevel.earth_guardian
            next_level_points = 1001
            progress_percentage = int(((points - 501) / 500) * 100)
        elif points >= 201:
            level = UserLevel.green_explorer
            next_level_points = 501
            progress_percentage = int(((points - 201) / 300) * 100)
        else:
            level = UserLevel.seedling
            next_level_points = 201
            progress_percentage = int((points / 200) * 100)

        # Determine Badges
        badges = [
            {"id": "first_step", "name": "First Step", "description": "Complete your first carbon footprint assessment.", "unlocked": assessments_count >= 1, "icon": "footprint"},
            {"id": "goal_getter", "name": "Goal Getter", "description": "Complete at least 3 sustainability goals.", "unlocked": goals_completed >= 3, "icon": "target"},
            {"id": "habit_hero", "name": "Habit Hero", "description": "Log at least 10 eco-habits.", "unlocked": habits_logged >= 10, "icon": "leaf"},
            {"id": "emission_reducer", "name": "Emission Reducer", "description": "Reduce your carbon footprint between assessments.", "unlocked": emission_reduction_tons > 0, "icon": "trending_down"},
            {"id": "assessment_streak", "name": "Assessment Pro", "description": "Complete 5 assessments.", "unlocked": assessments_count >= 5, "icon": "clipboard"},
        ]

        return {
            "level": level.value,
            "points": points,
            "next_level_points": next_level_points,
            "progress_percentage": min(100, max(0, progress_percentage)),
            "stats": {
                "assessments_count": assessments_count,
                "goals_completed": goals_completed,
                "habits_logged": habits_logged,
                "emission_reduction_tons": round(emission_reduction_tons, 2)
            },
            "badges": badges
        }
