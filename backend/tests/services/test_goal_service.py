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

def test_goal_not_found_raises_http_exception(db, test_user):
    import fastapi
    random_id = uuid.uuid4()
    with pytest.raises(fastapi.HTTPException) as exc_info:
        GoalService.get_goal(db, test_user.id, random_id)
    assert exc_info.value.status_code == 404

    with pytest.raises(fastapi.HTTPException) as exc_info:
        GoalService.update_goal(db, test_user.id, random_id, GoalUpdate(goal_name="Nonexistent"))
    assert exc_info.value.status_code == 404

    with pytest.raises(fastapi.HTTPException) as exc_info:
        GoalService.delete_goal(db, test_user.id, random_id)
    assert exc_info.value.status_code == 404

def test_expired_goal(db, test_user):
    # Target date in the past
    past_date = date.today() - timedelta(days=1)
    goal_in = GoalCreate(
        goal_name="Past Goal",
        target_emission_value=50.0,
        target_date=past_date
    )
    goal = GoalService.create_goal(db, test_user.id, goal_in)
    
    # get_goals should trigger expiration check
    goals = GoalService.get_goals(db, test_user.id)
    db.refresh(goal)
    assert goal.status == GoalStatus.expired

def test_goal_without_percentage_reduction(db, test_user):
    # Goal created directly with target_emission_value, no percentage
    goal_in = GoalCreate(
        goal_name="Direct Goal",
        target_emission_value=80.0,
        target_date=date.today() + timedelta(days=30)
    )
    goal = GoalService.create_goal(db, test_user.id, goal_in)
    assert goal.target_reduction_percentage is None
    assert goal.target_emission_value == 80.0

    # Get goals should not raise or guess progress incorrectly
    goals = GoalService.get_goals(db, test_user.id)
    assert goals[0].current_progress == 0.0

@patch("app.services.goal_service.AssessmentService.get_latest_assessment")
def test_create_goal_no_assessment(mock_get_latest, db, test_user):
    import fastapi
    # Mocking no assessment
    mock_get_latest.side_effect = fastapi.HTTPException(status_code=404, detail="No assessment")
    
    goal_in = GoalCreate(
        goal_name="No Assessment Goal",
        target_reduction_percentage=15.0,
        target_date=date.today() + timedelta(days=30)
    )
    goal = GoalService.create_goal(db, test_user.id, goal_in)
    assert goal.target_emission_value is None
