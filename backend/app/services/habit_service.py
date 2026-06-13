import uuid
from datetime import date, timedelta
from typing import List, Optional, Tuple, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.habit import Habit
from app.models.habit_definition import HabitDefinition
from app.models.enums import HabitType
from app.schemas.habit import HabitCreate, HabitUpdate

class HabitService:
    @staticmethod
    def log_habit(db: Session, user_id: uuid.UUID, habit_in: HabitCreate) -> Habit:
        # Lookup habit definition
        definition = db.query(HabitDefinition).filter(HabitDefinition.habit_type == habit_in.habit_type.value).first()
        carbon_saved = definition.carbon_saving_factor if definition else 0.0

        # Check if already logged for this date and type
        existing = db.query(Habit).filter(
            Habit.user_id == user_id,
            Habit.habit_type == habit_in.habit_type.value,
            Habit.activity_date == habit_in.activity_date
        ).first()

        if existing:
            # Update existing
            existing.notes = habit_in.notes
            existing.completed = True
            existing.carbon_saved = carbon_saved
            habit = existing
        else:
            habit = Habit(
                user_id=user_id,
                habit_type=habit_in.habit_type.value,
                activity_date=habit_in.activity_date,
                notes=habit_in.notes,
                completed=True,
                carbon_saved=carbon_saved
            )
            db.add(habit)

        db.commit()
        db.refresh(habit)
        return habit

    @staticmethod
    def get_habits(db: Session, user_id: uuid.UUID, start_date: Optional[date] = None, end_date: Optional[date] = None) -> List[Habit]:
        query = db.query(Habit).filter(Habit.user_id == user_id)
        if start_date:
            query = query.filter(Habit.activity_date >= start_date)
        if end_date:
            query = query.filter(Habit.activity_date <= end_date)
            
        return query.order_by(Habit.activity_date.desc()).all()

    @staticmethod
    def calculate_streak(db: Session, user_id: uuid.UUID) -> int:
        # Fetch distinct dates where a habit was completed
        dates = db.query(Habit.activity_date).filter(
            Habit.user_id == user_id,
            Habit.completed == True
        ).distinct().order_by(Habit.activity_date.desc()).all()
        
        if not dates:
            return 0
            
        dates = [d[0] for d in dates]
        streak = 0
        current_date = date.today()
        
        # If the most recent log isn't today or yesterday, the streak is broken.
        if dates[0] < current_date - timedelta(days=1):
            return 0
            
        expected_date = dates[0]
        
        for d in dates:
            if d == expected_date:
                streak += 1
                expected_date -= timedelta(days=1)
            else:
                break
                
        # If today is not logged, but yesterday is, streak is still alive, but streak count is based on days logged
        return streak

    @staticmethod
    def get_weekly_summary(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
        end_date = date.today()
        start_date = end_date - timedelta(days=6)
        
        habits = HabitService.get_habits(db, user_id, start_date=start_date, end_date=end_date)
        
        total_carbon_saved = sum((h.carbon_saved or 0.0) for h in habits if h.completed)
        completed_count = sum(1 for h in habits if h.completed)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "completed_habits": completed_count,
            "total_carbon_saved": total_carbon_saved
        }

    @staticmethod
    def get_monthly_summary(db: Session, user_id: uuid.UUID) -> Dict[str, Any]:
        end_date = date.today()
        start_date = end_date - timedelta(days=29)
        
        habits = HabitService.get_habits(db, user_id, start_date=start_date, end_date=end_date)
        
        total_carbon_saved = sum((h.carbon_saved or 0.0) for h in habits if h.completed)
        completed_count = sum(1 for h in habits if h.completed)
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "completed_habits": completed_count,
            "total_carbon_saved": total_carbon_saved
        }

    @staticmethod
    def update_habit(db: Session, user_id: uuid.UUID, habit_id: uuid.UUID, habit_in: HabitUpdate) -> Habit:
        habit = db.query(Habit).filter(Habit.user_id == user_id, Habit.id == habit_id).first()
        if not habit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        
        update_data = habit_in.model_dump(exclude_unset=True)
        if 'habit_type' in update_data:
            update_data['habit_type'] = update_data['habit_type'].value
            
            # Recalculate carbon saved if type changed
            definition = db.query(HabitDefinition).filter(HabitDefinition.habit_type == update_data['habit_type']).first()
            if definition:
                update_data['carbon_saved'] = definition.carbon_saving_factor

        for field, value in update_data.items():
            setattr(habit, field, value)
            
        db.commit()
        db.refresh(habit)
        return habit

    @staticmethod
    def delete_habit(db: Session, user_id: uuid.UUID, habit_id: uuid.UUID) -> None:
        habit = db.query(Habit).filter(Habit.user_id == user_id, Habit.id == habit_id).first()
        if not habit:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
        
        db.delete(habit)
        db.commit()
