from pydantic import BaseModel, Field, field_validator
import uuid
from datetime import datetime

from typing import Optional
from app.core.sanitizer import sanitize_text

class ChatRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    message: str = Field(..., min_length=1, max_length=1000)

    @field_validator('message')
    @classmethod
    def sanitize_message(cls, v: str) -> str:
        return sanitize_text(v)

class ChatMessage(BaseModel):
    id: uuid.UUID
    role: str
    message: str
    created_at: datetime

class ChatResponse(BaseModel):
    conversation_id: uuid.UUID
    message: str
    ai_message_id: uuid.UUID

class ChatHistoryItem(BaseModel):
    conversation_id: uuid.UUID
    created_at: datetime
    message_count: int
    latest_message: str

class ConversationHistoryResponse(BaseModel):
    conversation_id: uuid.UUID
    messages: list[ChatMessage]
