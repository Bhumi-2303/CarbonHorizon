import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.database import Base, get_db
from app.core.config import settings

# Setup test DB
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

client = TestClient(app)

print("--- AUDIT START ---")

# 1. Registration Flow
print("1. Registration")
reg_data = {
    "full_name": "Audit User",
    "email": "audit@example.com",
    "password": "Password123!"
}
res_reg = client.post("/api/v1/auth/register", json=reg_data)
print("Reg status:", res_reg.status_code)
print("Reg data:", res_reg.json())

# 2. Login Flow
print("\n2. Login")
log_data = {"email": "audit@example.com", "password": "Password123!"}
res_log = client.post("/api/v1/auth/login", json=log_data)
print("Log status:", res_log.status_code)
print("Log data:", res_log.json())
token = res_log.json().get("data", {}).get("access_token")

headers = {"Authorization": f"Bearer {token}"}

# 3. Protected Route
print("\n3. Protected Profile")
res_prof = client.get("/api/v1/auth/profile", headers=headers)
print("Profile status:", res_prof.status_code)

# 4. Carbon Assessment
print("\n4. Assessment")
assess_data = {
    "transport_mode": "car",
    "transport_distance_weekly": 100,
    "electricity_kwh_monthly": 200,
    "clean_energy_percentage": 0,
    "diet_type": "omnivore",
    "local_food_percentage": 10,
    "waste_bags_weekly": 2,
    "recycling_percentage": 10
}
res_ass = client.post("/api/v1/assessment", json=assess_data, headers=headers)
print("Assessment status:", res_ass.status_code)

# 5. Dashboard
print("\n5. Dashboard")
res_dash = client.get("/api/v1/dashboard", headers=headers)
print("Dashboard status:", res_dash.status_code)
if res_dash.status_code != 200:
    print("Dashboard error:", res_dash.json())

# 6. Goal Creation
print("\n6. Goals")
goal_data = {
    "goal_name": "Reduce Transport",
    "target_reduction_percentage": 10,
    "target_date": "2026-12-31T00:00:00Z"
}
res_goal = client.post("/api/v1/goals/", json=goal_data, headers=headers)
print("Goal status:", res_goal.status_code)

# 7. Habit Creation
print("\n7. Habit")
habit_data = {
    "category": "transport",
    "impact_level": "medium",
    "description": "Biked to work"
}
res_habit = client.post("/api/v1/habits/log", json=habit_data, headers=headers)
print("Habit status:", res_habit.status_code)

# 8. Forecast Generation
print("\n8. Forecast")
res_fore = client.get("/api/v1/forecast/trajectory", headers=headers)
print("Forecast status:", res_fore.status_code)

# 9. AI Coach
print("\n9. Coach")
coach_data = {"message": "How can I reduce emissions?"}
res_coach = client.post("/api/v1/coach/chat", json=coach_data, headers=headers)
print("Coach status:", res_coach.status_code)
if res_coach.status_code != 200:
    print("Coach err:", res_coach.json())

print("--- AUDIT END ---")
