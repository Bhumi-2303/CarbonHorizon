import pytest
from app.services.habit_service import HabitService
from app.schemas.habit import HabitCreate
from app.models.user import User
import uuid
from datetime import date, timedelta

@pytest.fixture
def test_user(db):
    user = User(
        email=f"habit_{uuid.uuid4()}@example.com",
        password_hash="hash",
        full_name="Habit User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def test_log_and_get_habit(db, test_user):
    habit_in = HabitCreate(
        habit_type="recycling",
        activity_date=date.today(),
        notes="Recycled paper"
    )
    
    habit = HabitService.log_habit(db, test_user.id, habit_in)
    assert habit.id is not None
    assert habit.notes == "Recycled paper"
    
    habits = HabitService.get_habits(db, test_user.id)
    assert len(habits) >= 1

def test_streak_calculation(db, test_user):
    today = date.today()
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=today))
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=today - timedelta(days=1)))
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=today - timedelta(days=2)))
    
    # Missing day 3, but logged day 4 (should break streak)
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=today - timedelta(days=4)))
    
    streak = HabitService.calculate_streak(db, test_user.id)
    assert streak == 3
    
def test_delete_habit(db, test_user):
    habit_in = HabitCreate(habit_type="recycling", activity_date=date.today())
    habit = HabitService.log_habit(db, test_user.id, habit_in)
    
    HabitService.delete_habit(db, test_user.id, habit.id)
    
    habits = HabitService.get_habits(db, test_user.id)
    assert len(habits) == 0
