import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from fastapi.testclient import TestClient

from main import app
from app.models.enums import ConversationRole
from app.models.ai_conversation import AIConversation

@pytest.fixture
def mock_gemini():
    with patch("app.services.coach_service.genai.GenerativeModel") as mock_model, \
         patch("app.services.coach_service.settings.GEMINI_API_KEY", "dummy_key"):
        mock_instance = MagicMock()
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "This is a mocked AI response."
        
        mock_session.send_message.return_value = mock_response
        mock_instance.start_chat.return_value = mock_session
        mock_model.return_value = mock_instance
        yield mock_model

def test_chat_with_coach(client, db, auth_headers, mock_gemini):
    conv_id = str(uuid4())
    payload = {
        "conversation_id": conv_id,
        "message": "How can I improve my footprint?"
    }
    
    resp = client.post("/api/v1/coach/chat", json=payload, headers=auth_headers)
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
