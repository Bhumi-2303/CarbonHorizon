import uuid
from datetime import date
from typing import List

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.models.enums import GoalStatus
from app.schemas.goal import GoalCreate, GoalUpdate
from app.services.assessment_service import AssessmentService

class GoalService:
    @staticmethod
    def create_goal(db: Session, user_id: uuid.UUID, goal_in: GoalCreate) -> Goal:
        # If target_emission_value is not provided but percentage is, calculate it
        target_val = goal_in.target_emission_value
        if target_val is None and goal_in.target_reduction_percentage is not None:
            try:
                latest = AssessmentService.get_latest_assessment(db, user_id)
                current_emission = latest["total_emission"]
                target_val = current_emission * (1.0 - (goal_in.target_reduction_percentage / 100.0))
            except HTTPException:
                # No previous assessment, default to a sensible or pass
                pass
                
        goal = Goal(
            user_id=user_id,
            goal_name=goal_in.goal_name,
            goal_description=goal_in.goal_description,
            target_reduction_percentage=goal_in.target_reduction_percentage,
            target_emission_value=target_val,
            target_date=goal_in.target_date,
            status=GoalStatus.active,
            current_progress=0.0
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def get_goals(db: Session, user_id: uuid.UUID) -> List[Goal]:
        goals = db.query(Goal).filter(Goal.user_id == user_id).all()
        
        # Calculate progress
        try:
            latest = AssessmentService.get_latest_assessment(db, user_id)
            current_emission = latest["total_emission"]
        except HTTPException:
            current_emission = None
            
        today = date.today()
        changed = False
        
        for goal in goals:
            if goal.status == GoalStatus.active:
                # Check expiration
                if goal.target_date and goal.target_date < today:
                    goal.status = GoalStatus.expired
                    changed = True
                
                # Check progress if we have a current_emission
                elif current_emission is not None and goal.target_emission_value is not None:
                    # Simple heuristic: if current <= target, progress is 100
                    if current_emission <= goal.target_emission_value:
                        goal.current_progress = 100.0
                        goal.status = GoalStatus.completed
                        changed = True
                    else:
                        # What was the starting value? We don't have baseline explicitly, 
                        # but we can assume we only move forward. Let's just track if they hit the absolute target.
                        # For a continuous percentage, let's look for a naive way or just set 0-99 based on distance.
                        # If we assume an arbitrary baseline (e.g. target + 20%), this is hard to guess.
                        # If target_reduction_percentage is available, baseline ≈ target / (1 - pct/100).
                        if goal.target_reduction_percentage:
                            baseline = goal.target_emission_value / (1.0 - (goal.target_reduction_percentage / 100.0))
                            if baseline > goal.target_emission_value:
                                progress = 100.0 * (baseline - current_emission) / (baseline - goal.target_emission_value)
                                goal.current_progress = max(0.0, min(99.9, progress))
                                changed = True
                        else:
                            # If no percentage, just basic indication if moving towards it? Let's leave progress unchanged or update it to a generic value.
                            # Just update to 0.0 unless completed to avoid wild guesses.
                            pass

        if changed:
            db.commit()
            for goal in goals:
                db.refresh(goal)
                
        # Return sorted by created_at desc (or just as-is)
        return sorted(goals, key=lambda g: g.created_at, reverse=True)

    @staticmethod
    def get_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> Goal:
        goal = db.query(Goal).filter(Goal.user_id == user_id, Goal.id == goal_id).first()
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        # Ensure it's up to date by running the same logic as get_goals
        # A simpler way is to just call get_goals and filter, since get_goals auto-updates.
        goals = GoalService.get_goals(db, user_id)
        for g in goals:
            if g.id == goal_id:
                return g
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")

    @staticmethod
    def get_active_goals(db: Session, user_id: uuid.UUID) -> List[Goal]:
        goals = GoalService.get_goals(db, user_id)
        return [g for g in goals if g.status == GoalStatus.active]

    @staticmethod
    def update_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID, goal_in: GoalUpdate) -> Goal:
        goal = db.query(Goal).filter(Goal.user_id == user_id, Goal.id == goal_id).first()
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        
        update_data = goal_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(goal, field, value)
            
        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def delete_goal(db: Session, user_id: uuid.UUID, goal_id: uuid.UUID) -> None:
        goal = db.query(Goal).filter(Goal.user_id == user_id, Goal.id == goal_id).first()
        if not goal:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Goal not found")
        
        db.delete(goal)
        db.commit()
