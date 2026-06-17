import time
import pytest
from uuid import uuid4
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_gemini():
    with patch("app.services.coach_service.genai.Client") as mock_client_class, \
         patch("app.services.coach_service.settings.GEMINI_API_KEY", "dummy_key"):
        mock_client = MagicMock()
        mock_chats = MagicMock()
        mock_chat_session = MagicMock()
        mock_response = MagicMock()
        
        mock_response.text = "This is a mocked AI response."
        mock_chat_session.send_message.return_value = mock_response
        mock_chats.create.return_value = mock_chat_session
        mock_client.chats = mock_chats
        mock_client_class.return_value = mock_client
        yield mock_client_class

def test_full_user_journey(client, db, mock_gemini):
    email = f"journey_{uuid4().hex[:8]}@example.com"
    password = "StrongPassword123!"

    # 1. Register & Login -> JWT stored
    start_time = time.time()
    reg_res = client.post("/api/v1/auth/register", json={
        "full_name": "Journey User",
        "email": email,
        "password": password
    })
    assert reg_res.status_code == 201
    assert (time.time() - start_time) < 2.0

    start_time = time.time()
    login_res = client.post("/api/v1/auth/login", json={
        "email": email,
        "password": password
    })
    assert login_res.status_code == 200
    assert (time.time() - start_time) < 2.0

    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Submit assessment -> correct emissions
    start_time = time.time()
    assess_res = client.post("/api/v1/assessment/create", json={
        "transport_mode": "car",
        "distance_km": 1000,
        "electricity_kwh": 500,
        "ac_hours": 100,
        "lpg_usage": 15,
        "solar_usage": False,
        "diet_type": "non_vegetarian",
        "recycling_score": 1,
        "plastic_usage_score": 1,
        "household_size": 2,
        "assessment_period": "monthly"
    }, headers=headers)
    assert assess_res.status_code == 201
    assess_data = assess_res.json()["data"]
    assert assess_data["carbon_score"] > 0
    assert (time.time() - start_time) < 2.0

    # 3. View dashboard -> latest assessment shown
    start_time = time.time()
    hist_res = client.get("/api/v1/assessment/history", headers=headers)
    assert hist_res.status_code == 200
    assert len(hist_res.json()["data"]) >= 1
    assert hist_res.json()["data"][0]["assessment_id"] == assess_data["assessment_id"]
    assert (time.time() - start_time) < 2.0

    # 4. Run simulation -> reduction calculated
    start_time = time.time()
    sim_res = client.post("/api/v1/simulator/run", json={
        "scenario_name": "car_to_bus",
        "transport_mode": "car",
        "distance_km": 1000,
        "electricity_kwh": 500,
        "ac_hours": 100,
        "lpg_usage": 15,
        "solar_usage": False,
        "diet_type": "non_vegetarian",
        "recycling_score": 1,
        "plastic_usage_score": 1,
        "household_size": 2,
        "changes": {
            "transport": {"new_mode": "bus"}
        }
    }, headers=headers)
    assert sim_res.status_code == 200
    sim_data = sim_res.json()["data"]
    assert sim_data["carbon_saved"] > 0
    assert (time.time() - start_time) < 2.0

    # 5. Generate forecast -> 3 scenarios at 3/6/12 months
    start_time = time.time()
    for ftype in ["current_path", "recommended_path", "custom_path"]:
        fc_res = client.post("/api/v1/forecast/generate", json={
            "forecast_type": ftype
        }, headers=headers)
        assert fc_res.status_code == 201
        fc_data = fc_res.json()["data"]
        assert len(fc_data["forecast_points"]) == 3
        # Ensure month offsets are 3, 6, 12
        offsets = [p["month_offset"] for p in fc_data["forecast_points"]]
        assert 3 in offsets
        assert 6 in offsets
        assert 12 in offsets
    assert (time.time() - start_time) < 2.0

    # 6. Ask AI coach question -> response received without emission numbers
    conv_id = str(uuid4())
    start_time = time.time()
    coach_res = client.post("/api/v1/coach/chat", json={
        "conversation_id": conv_id,
        "message": "How can I improve my footprint?"
    }, headers=headers)
    assert coach_res.status_code == 200
    coach_data = coach_res.json()["data"]
    assert "This is a mocked AI response" in coach_data["message"]
    # Check that no numbers are in the AI response because they are mocked
    assert not any(char.isdigit() for char in coach_data["message"])
    assert (time.time() - start_time) < 2.0

    # 7. Create goal -> log habit -> streak = 1
    start_time = time.time()
    goal_res = client.post("/api/v1/goals/", json={
        "goal_name": "Reduce Plastic",
        "target_reduction_percentage": 10.0,
        "target_date": "2027-01-01"
    }, headers=headers)
    assert goal_res.status_code == 201
    assert (time.time() - start_time) < 2.0

    import datetime
    start_time = time.time()
    habit_res = client.post("/api/v1/habits/log", json={
        "habit_type": "recycling",
        "activity_date": datetime.date.today().isoformat(),
        "notes": "Did recycling"
    }, headers=headers)
    assert habit_res.status_code == 201
    assert (time.time() - start_time) < 2.0

    start_time = time.time()
    streak_res = client.get("/api/v1/habits/streak", headers=headers)
    assert streak_res.status_code == 200
    assert streak_res.json()["data"]["streak"] == 1
    assert (time.time() - start_time) < 2.0
