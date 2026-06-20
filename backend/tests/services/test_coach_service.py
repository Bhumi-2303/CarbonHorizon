import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient

from main import app
from app.models.enums import ConversationRole
from app.models.ai_conversation import AIConversation

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

def test_chat_with_coach(client, db, auth_headers, mock_gemini):
    conv_id = str(uuid4())
    payload = {
        "conversation_id": conv_id,
        "message": "How can I improve my footprint?"
    }
    
    resp = client.post("/api/v1/coach/chat", json=payload, headers=auth_headers)
    print(resp.json())
    assert resp.status_code == 200
    data = resp.json()["data"]
    
    assert data["conversation_id"] == conv_id
    assert data["message"] == "This is a mocked AI response."
    
    # Check db
    from uuid import UUID
    convs = db.query(AIConversation).filter_by(conversation_id=UUID(conv_id)).all()
    assert len(convs) == 2
    assert (convs[0].role if isinstance(convs[0].role, str) else convs[0].role.value) == ConversationRole.user.value
    assert (convs[1].role if isinstance(convs[1].role, str) else convs[1].role.value) == ConversationRole.assistant.value

def test_get_chat_history(client, db, auth_headers, mock_gemini):
    conv_id = str(uuid4())
    payload = {
        "conversation_id": conv_id,
        "message": "First message"
    }
    client.post("/api/v1/coach/chat", json=payload, headers=auth_headers)
    
    resp = client.get(f"/api/v1/coach/history?conversation_id={conv_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    
    assert data["conversation_id"] == conv_id
    assert len(data["messages"]) == 2
    assert data["messages"][0]["message"] == "First message"
    assert data["messages"][1]["message"] == "This is a mocked AI response."

def test_chat_with_coach_retry_fallback(client, db, auth_headers, mock_gemini):
    from google.genai import errors
    from fastapi.testclient import TestClient
    
    mock_client_class = mock_gemini
    mock_chat_session = mock_client_class.return_value.chats.create.return_value
    
    import requests
    resp_obj = requests.Response()
    resp_obj.status_code = 503
    resp_obj._content = b'{"error": {"message": "This model is currently experiencing high demand"}}'
    api_error = errors.APIError(code=503, response=resp_obj)
    
    # Make it fail twice, then succeed
    mock_response = MagicMock()
    mock_response.text = "This is a mocked fallback response."
    mock_chat_session.send_message.side_effect = [api_error, api_error, mock_response]
    
    conv_id = str(uuid4())
    payload = {
        "conversation_id": conv_id,
        "message": "Testing fallback"
    }
    
    # We need to mock time.sleep so the test doesn't take 7 seconds
    with patch("time.sleep"):
        resp = client.post("/api/v1/coach/chat", json=payload, headers=auth_headers)
        
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["message"] == "This is a mocked fallback response."
    assert mock_chat_session.send_message.call_count == 3
    
def test_chat_with_coach_exhaust_retries(client, db, auth_headers, mock_gemini):
    from google.genai import errors
    
    mock_client_class = mock_gemini
    mock_chat_session = mock_client_class.return_value.chats.create.return_value
    import requests
    resp_obj = requests.Response()
    resp_obj.status_code = 503
    resp_obj._content = b'{"error": {"message": "High demand"}}'
    api_error = errors.APIError(code=503, response=resp_obj)
    mock_chat_session.send_message.side_effect = [api_error, api_error, api_error]
    
    payload = {
        "message": "Testing exhaust"
    }
    
    with patch("time.sleep"):
        resp = client.post("/api/v1/coach/chat", json=payload, headers=auth_headers)
        
    assert resp.status_code == 503
    assert resp.json()["message"] == "The AI Coach is currently busy. Please try again in a few moments."
    assert mock_chat_session.send_message.call_count == 3

def test_coach_empty_payload(client, auth_headers):
    resp = client.post("/api/v1/coach/chat", json={}, headers=auth_headers)
    assert resp.status_code == 422 # FastAPI validation error

def test_coach_invalid_payload(client, auth_headers):
    resp = client.post("/api/v1/coach/chat", json={"invalid": "payload"}, headers=auth_headers)
    assert resp.status_code == 422

def test_coach_excessively_long_payload(client, auth_headers):
    payload = {
        "message": "A" * 10001
    }
    resp = client.post("/api/v1/coach/chat", json=payload, headers=auth_headers)
    assert resp.status_code in [400, 422, 413] # Depending on validation, should not be 500

def test_coach_rate_limit(client, db, auth_headers, mock_gemini):
    payload = {"message": "Test"}
    
    # Send enough requests to trigger a rate limit.
    # Assuming standard rate limiter blocks after a few requests in tests.
    responses = []
    for _ in range(30):
        resp = client.post("/api/v1/coach/chat", json=payload, headers=auth_headers)
        responses.append(resp.status_code)
    
    # We expect either all 200s (if rate limit is not active in test) or at least one 429
    # Just asserting it doesn't crash with 500.
    assert all(status in [200, 429] for status in responses)

def test_coach_gemini_api_key_missing(client, auth_headers):
    with patch("app.services.coach_service.settings.GEMINI_API_KEY", ""), \
         patch.dict("os.environ", {}, clear=True):
        resp = client.post("/api/v1/coach/chat", json={"message": "hello"}, headers=auth_headers)
        assert resp.status_code == 500
        assert "Gemini API Key is missing" in resp.json()["message"]

def test_coach_non_retryable_api_error(client, auth_headers, mock_gemini):
    from google.genai import errors
    import requests
    mock_client_class = mock_gemini
    mock_chat_session = mock_client_class.return_value.chats.create.return_value
    resp_obj = requests.Response()
    resp_obj.status_code = 403
    resp_obj._content = b'{"error": {"message": "Invalid key"}}'
    api_error = errors.APIError(code=403, response=resp_obj)
    mock_chat_session.send_message.side_effect = api_error

    resp = client.post("/api/v1/coach/chat", json={"message": "hello"}, headers=auth_headers)
    assert resp.status_code == 503
    assert "The AI Coach is temporarily unavailable" in resp.json()["message"]

def test_coach_exhaust_retries_429(client, auth_headers, mock_gemini):
    from google.genai import errors
    import requests
    mock_client_class = mock_gemini
    mock_chat_session = mock_client_class.return_value.chats.create.return_value
    resp_obj = requests.Response()
    resp_obj.status_code = 429
    resp_obj._content = b'{"error": {"message": "Quota exceeded"}}'
    api_error = errors.APIError(code=429, response=resp_obj)
    mock_chat_session.send_message.side_effect = [api_error, api_error, api_error]

    with patch("time.sleep"):
        resp = client.post("/api/v1/coach/chat", json={"message": "hello"}, headers=auth_headers)
    assert resp.status_code == 429

def test_coach_exhaust_retries_504(client, auth_headers, mock_gemini):
    from google.genai import errors
    import requests
    mock_client_class = mock_gemini
    mock_chat_session = mock_client_class.return_value.chats.create.return_value
    resp_obj = requests.Response()
    resp_obj.status_code = 504
    resp_obj._content = b'{"error": {"message": "Gateway timeout"}}'
    api_error = errors.APIError(code=504, response=resp_obj)
    mock_chat_session.send_message.side_effect = [api_error, api_error, api_error]

    with patch("time.sleep"):
        resp = client.post("/api/v1/coach/chat", json={"message": "hello"}, headers=auth_headers)
    assert resp.status_code == 504

def test_coach_unexpected_exception(client, auth_headers, mock_gemini):
    mock_client_class = mock_gemini
    mock_chat_session = mock_client_class.return_value.chats.create.return_value
    mock_chat_session.send_message.side_effect = Exception("unexpected error")

    resp = client.post("/api/v1/coach/chat", json={"message": "hello"}, headers=auth_headers)
    assert resp.status_code == 500
