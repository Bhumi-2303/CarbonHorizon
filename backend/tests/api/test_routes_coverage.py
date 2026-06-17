import pytest
import uuid
from datetime import date
from fastapi.testclient import TestClient
from app.models.goal import Goal
from app.models.habit import Habit
from app.models.habit_definition import HabitDefinition
from app.services.goal_service import GoalService
from app.services.habit_service import HabitService

# ─── Goals Route Tests ────────────────────────────────────────────────────────

def test_goals_endpoints(client: TestClient, auth_headers: dict):
    # 1. Create a goal
    payload = {
        "goal_name": "Reduce Energy footprint",
        "goal_description": "Reduce my energy consumption",
        "target_reduction_percentage": 10.0,
        "target_emission_value": 150.0,
        "target_date": str(date.today() + __import__("datetime").timedelta(days=30))
    }
    r = client.post("/api/v1/goals/", json=payload, headers=auth_headers)
    assert r.status_code == 201
    goal_id = r.json()["data"]["id"]
    assert goal_id is not None

    # 2. Get goals list
    r_list = client.get("/api/v1/goals/", headers=auth_headers)
    assert r_list.status_code == 200
    assert len(r_list.json()["data"]) >= 1

    # 3. Get active goals
    r_active = client.get("/api/v1/goals/active", headers=auth_headers)
    assert r_active.status_code == 200
    assert len(r_active.json()["data"]) >= 1

    # 4. Get goal by id
    r_detail = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers)
    assert r_detail.status_code == 200
    assert r_detail.json()["data"]["goal_name"] == "Reduce Energy footprint"

    # 5. Patch goal
    r_patch = client.patch(f"/api/v1/goals/{goal_id}", json={"current_progress": 50.0, "status": "completed"}, headers=auth_headers)
    assert r_patch.status_code == 200
    assert r_patch.json()["data"]["current_progress"] == 50.0
    assert r_patch.json()["data"]["status"] == "completed"

    # 6. Delete goal
    r_del = client.delete(f"/api/v1/goals/{goal_id}", headers=auth_headers)
    assert r_del.status_code == 204

    # 7. Get deleted goal returns 404
    r_gone = client.get(f"/api/v1/goals/{goal_id}", headers=auth_headers)
    assert r_gone.status_code == 404

# ─── Habits Route Tests ────────────────────────────────────────────────────────

def test_habits_endpoints(client: TestClient, db, test_user, auth_headers: dict):
    # Ensure habit definitions exist
    def1 = db.query(HabitDefinition).filter(HabitDefinition.habit_type == "recycling").first()
    if not def1:
        db.add(HabitDefinition(habit_type="recycling", carbon_saving_factor=1.5, unit="kg CO₂e per trip", description="Recycling"))
        db.commit()

    # 1. Log habit
    payload = {
        "habit_type": "recycling",
        "activity_date": str(date.today()),
        "notes": "Logged transit habit"
    }
    r = client.post("/api/v1/habits/log", json=payload, headers=auth_headers)
    assert r.status_code == 201
    habit_id = r.json()["data"]["id"]

    # 2. Get list of habits
    r_list = client.get(f"/api/v1/habits/?start_date={date.today()}&end_date={date.today()}", headers=auth_headers)
    assert r_list.status_code == 200
    assert len(r_list.json()["data"]) >= 1

    # 3. Get streak
    r_streak = client.get("/api/v1/habits/streak", headers=auth_headers)
    assert r_streak.status_code == 200
    assert "streak" in r_streak.json()["data"]

    # 4. Get summaries
    r_week = client.get("/api/v1/habits/summary/weekly", headers=auth_headers)
    assert r_week.status_code == 200
    assert "completed_habits" in r_week.json()["data"]

    r_month = client.get("/api/v1/habits/summary/monthly", headers=auth_headers)
    assert r_month.status_code == 200
    assert "completed_habits" in r_month.json()["data"]

    # 5. Patch habit
    r_patch = client.patch(f"/api/v1/habits/{habit_id}", json={"notes": "Updated notes"}, headers=auth_headers)
    assert r_patch.status_code == 200
    assert r_patch.json()["data"]["notes"] == "Updated notes"

    # 6. Delete habit
    r_del = client.delete(f"/api/v1/habits/{habit_id}", headers=auth_headers)
    assert r_del.status_code == 204

# ─── Simulator Route Tests ─────────────────────────────────────────────────────

def test_simulator_endpoints(client: TestClient, auth_headers: dict):
    # Test listing simulator history (should be empty initially)
    r_hist = client.get("/api/v1/simulator/history", headers=auth_headers)
    assert r_hist.status_code == 200
    assert len(r_hist.json()["data"]) == 0

    # Test get non-existent simulation
    r_none = client.get(f"/api/v1/simulator/{uuid.uuid4()}", headers=auth_headers)
    assert r_none.status_code == 404

    # Test delete non-existent simulation
    r_del_none = client.delete(f"/api/v1/simulator/{uuid.uuid4()}", headers=auth_headers)
    assert r_del_none.status_code == 404

# ─── Dashboard Route Tests ─────────────────────────────────────────────────────

def test_dashboard_endpoints(client: TestClient, auth_headers: dict):
    r_sum = client.get("/api/v1/dashboard/summary", headers=auth_headers)
    assert r_sum.status_code == 200
    assert r_sum.json() == {"detail": "not implemented"}

    r_hist = client.get("/api/v1/dashboard/history", headers=auth_headers)
    assert r_hist.status_code == 200
    assert r_hist.json() == {"detail": "not implemented"}

    r_brk = client.get("/api/v1/dashboard/breakdown", headers=auth_headers)
    assert r_brk.status_code == 200
    assert r_brk.json() == {"detail": "not implemented"}
