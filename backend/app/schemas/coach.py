from pydantic import BaseModel, Field
import uuid
from datetime import datetime

from typing import Optional

class ChatRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    message: str = Field(..., min_length=1)

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
