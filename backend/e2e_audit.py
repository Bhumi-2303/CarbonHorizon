import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app
from app.db.base import Base
from app.core.security import get_db

engine = create_engine("sqlite:///./test_audit.db", connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app, raise_server_exceptions=False)

print("--- AUDIT START ---")

print("\n1. Registration")
res_reg = client.post("/api/v1/auth/register", json={
    "full_name": "Audit User", "email": "audit@example.com", "password": "Password123!"
})
print("Reg status:", res_reg.status_code)
print("Reg content:", res_reg.text[:100])

print("\n2. Login")
res_log = client.post("/api/v1/auth/login", json={"email": "audit@example.com", "password": "Password123!"})
print("Log status:", res_log.status_code)
token = res_log.json().get("data", {}).get("access_token") if res_log.status_code == 200 else "FAKE_TOKEN"

headers = {"Authorization": f"Bearer {token}"}

print("\n3. Protected Profile")
res_prof = client.get("/api/v1/auth/profile", headers=headers)
print("Profile status:", res_prof.status_code)

print("\n4. Assessment")
res_ass = client.post("/api/v1/assessment/", json={
    "transport_mode": "car", "transport_distance_weekly": 100,
    "electricity_kwh_monthly": 200, "clean_energy_percentage": 0,
    "diet_type": "omnivore", "local_food_percentage": 10,
    "waste_bags_weekly": 2, "recycling_percentage": 10
}, headers=headers)
print("Assessment status:", res_ass.status_code)
if res_ass.status_code != 200:
    print("Assessment content:", res_ass.text[:100])

print("\n5. Dashboard")
res_dash = client.get("/api/v1/dashboard/", headers=headers)
print("Dashboard status:", res_dash.status_code)

print("\n6. Goals")
res_goal = client.post("/api/v1/goals/", json={
    "goal_name": "Reduce Transport", "target_reduction_percentage": 10,
    "target_date": "2026-12-31T00:00:00Z"
}, headers=headers)
print("Goal status:", res_goal.status_code)

print("\n7. Habit")
res_habit = client.post("/api/v1/habits/log", json={
    "category": "transport", "impact_level": "medium", "description": "Biked to work"
}, headers=headers)
print("Habit status:", res_habit.status_code)

print("\n8. Forecast")
res_fore = client.get("/api/v1/forecast/trajectory", headers=headers)
print("Forecast status:", res_fore.status_code)

print("\n9. Coach")
res_coach = client.post("/api/v1/coach/chat", json={"message": "Hi"}, headers=headers)
print("Coach status:", res_coach.status_code)
if res_coach.status_code != 200:
    print("Coach content:", res_coach.text[:200])

print("--- AUDIT END ---")
