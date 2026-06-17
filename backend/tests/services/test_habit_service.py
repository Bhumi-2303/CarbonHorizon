import pytest
from app.services.habit_service import HabitService
from app.schemas.habit import HabitCreate, HabitUpdate
from app.models.user import User
from app.models.habit_definition import HabitDefinition
from fastapi import HTTPException
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
    
    # Add a couple of habit definitions if not present to check carbon_saving_factor lookup
    def1 = db.query(HabitDefinition).filter(HabitDefinition.habit_type == "recycling").first()
    if not def1:
        def1 = HabitDefinition(habit_type="recycling", carbon_saving_factor=1.5, unit="kg CO₂e per trip", description="Recycling")
        db.add(def1)
    else:
        def1.carbon_saving_factor = 1.5

    def2 = db.query(HabitDefinition).filter(HabitDefinition.habit_type == "public_transport").first()
    if not def2:
        def2 = HabitDefinition(habit_type="public_transport", carbon_saving_factor=3.0, unit="kg CO₂e per trip", description="Transit")
        db.add(def2)
    else:
        def2.carbon_saving_factor = 3.0
    
    db.commit()
    db.refresh(user)
    return user

def test_log_and_get_habit(db, test_user):
    # Log new habit
    habit_in = HabitCreate(
        habit_type="recycling",
        activity_date=date.today(),
        notes="Recycled paper"
    )
    
    habit = HabitService.log_habit(db, test_user.id, habit_in)
    assert habit.id is not None
    assert habit.notes == "Recycled paper"
    assert habit.carbon_saved == 1.5
    
    # Log duplicate habit to test update branch
    habit_dup = HabitCreate(
        habit_type="recycling",
        activity_date=date.today(),
        notes="Recycled paper duplicate"
    )
    habit_updated = HabitService.log_habit(db, test_user.id, habit_dup)
    assert habit_updated.id == habit.id
    assert habit_updated.notes == "Recycled paper duplicate"

    # Get habits with date bounds
    habits = HabitService.get_habits(db, test_user.id, start_date=date.today() - timedelta(days=1), end_date=date.today())
    assert len(habits) >= 1

def test_streak_calculation_empty(db, test_user):
    # Test empty streak
    assert HabitService.calculate_streak(db, test_user.id) == 0

def test_streak_calculation_broken_past(db, test_user):
    # Log older habit (e.g. 5 days ago) but nothing recently
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=date.today() - timedelta(days=5)))
    assert HabitService.calculate_streak(db, test_user.id) == 0

def test_streak_calculation(db, test_user):
    today = date.today()
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=today))
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=today - timedelta(days=1)))
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=today - timedelta(days=2)))
    
    # Missing day 3, but logged day 4 (should break streak)
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=today - timedelta(days=4)))
    
    streak = HabitService.calculate_streak(db, test_user.id)
    assert streak == 3

def test_summaries(db, test_user):
    today = date.today()
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=today))
    HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="public_transport", activity_date=today - timedelta(days=2)))

    weekly = HabitService.get_weekly_summary(db, test_user.id)
    assert weekly["completed_habits"] == 2
    assert weekly["total_carbon_saved"] == 4.5

    monthly = HabitService.get_monthly_summary(db, test_user.id)
    assert monthly["completed_habits"] == 2
    assert monthly["total_carbon_saved"] == 4.5

def test_update_habit(db, test_user):
    habit = HabitService.log_habit(db, test_user.id, HabitCreate(habit_type="recycling", activity_date=date.today()))
    
    # Update type to public_transport
    update_in = HabitUpdate(habit_type="public_transport", notes="Took bus instead")
    updated = HabitService.update_habit(db, test_user.id, habit.id, update_in)
    assert updated.habit_type == "public_transport"
    assert updated.carbon_saved == 3.0
    assert updated.notes == "Took bus instead"

    # Test update habit not found
    with pytest.raises(HTTPException) as exc_info:
        HabitService.update_habit(db, test_user.id, uuid.uuid4(), update_in)
    assert exc_info.value.status_code == 404

def test_delete_habit_not_found(db, test_user):
    with pytest.raises(HTTPException) as exc_info:
        HabitService.delete_habit(db, test_user.id, uuid.uuid4())
    assert exc_info.value.status_code == 404

def test_delete_habit(db, test_user):
    habit_in = HabitCreate(habit_type="recycling", activity_date=date.today())
    habit = HabitService.log_habit(db, test_user.id, habit_in)
    
    HabitService.delete_habit(db, test_user.id, habit.id)
    
    habits = HabitService.get_habits(db, test_user.id)
    assert len(habits) == 0
