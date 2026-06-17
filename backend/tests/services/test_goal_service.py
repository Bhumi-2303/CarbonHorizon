import pytest
from unittest.mock import patch
from datetime import date, timedelta
from app.services.goal_service import GoalService
from app.schemas.goal import GoalCreate, GoalUpdate
from app.models.enums import GoalStatus
from app.models.user import User
import uuid

@pytest.fixture
def test_user(db):
    user = User(
        email=f"goal_{uuid.uuid4()}@example.com",
        password_hash="hash",
        full_name="Goal User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@patch("app.services.goal_service.AssessmentService.get_latest_assessment")
def test_create_and_get_goal(mock_get_latest, db, test_user):
    mock_get_latest.return_value = {"total_emission": 100.0}
    
    target_date = date.today() + timedelta(days=30)
    goal_in = GoalCreate(
        goal_name="Test Goal",
        target_reduction_percentage=10.0,
        target_date=target_date
    )
    
    goal = GoalService.create_goal(db, test_user.id, goal_in)
    assert goal.id is not None
    assert goal.target_emission_value == 90.0 # 100 - 10%
    
    fetched = GoalService.get_goal(db, test_user.id, goal.id)
    assert fetched.id == goal.id
    
    goals = GoalService.get_active_goals(db, test_user.id)
    assert len(goals) >= 1

@patch("app.services.goal_service.AssessmentService.get_latest_assessment")
def test_goal_progress_update(mock_get_latest, db, test_user):
    # Baseline was 100, target is 90
    mock_get_latest.return_value = {"total_emission": 100.0}
    target_date = date.today() + timedelta(days=30)
    goal_in = GoalCreate(goal_name="Progress Goal", target_reduction_percentage=10.0, target_date=target_date)
    goal = GoalService.create_goal(db, test_user.id, goal_in)
    
    # Now assessment drops to 95 (50% progress)
    mock_get_latest.return_value = {"total_emission": 95.0}
    GoalService.get_goals(db, test_user.id)
    
    db.refresh(goal)
    assert 49.0 <= goal.current_progress <= 51.0
    
    # Now assessment drops to 85 (completed)
    mock_get_latest.return_value = {"total_emission": 85.0}
    GoalService.get_goals(db, test_user.id)
    
    db.refresh(goal)
    assert goal.status == GoalStatus.completed

def test_update_and_delete_goal(db, test_user):
    target_date = date.today() + timedelta(days=30)
    goal_in = GoalCreate(goal_name="To Update", target_reduction_percentage=10.0, target_date=target_date)
    goal = GoalService.create_goal(db, test_user.id, goal_in)
    
    update_in = GoalUpdate(goal_name="Updated Name")
    updated = GoalService.update_goal(db, test_user.id, goal.id, update_in)
    assert updated.goal_name == "Updated Name"
    
    GoalService.delete_goal(db, test_user.id, goal.id)
    
    import fastapi
    with pytest.raises(fastapi.HTTPException):
        GoalService.get_goal(db, test_user.id, goal.id)
