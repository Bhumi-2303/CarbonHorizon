from pydantic import BaseModel, Field, field_validator
import uuid
from datetime import datetime

from typing import Optional
from app.core.sanitizer import sanitize_text, sanitize_html_output


class ChatRequest(BaseModel):
    conversation_id: Optional[uuid.UUID] = None
    message: str = Field(..., min_length=1, max_length=2000)
    honeypot: Optional[str] = Field(None, max_length=100)
    turnstile_token: Optional[str] = Field(None, max_length=2048)

    @field_validator("honeypot")
    @classmethod
    def validate_honeypot(cls, v: Optional[str]) -> Optional[str]:
        if v and v.strip():
            raise ValueError("Bot detected via honeypot")
        return v

    @field_validator("message")
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

    @field_validator("message")
    @classmethod
    def sanitize_output_message(cls, v: str) -> str:
        return sanitize_html_output(v)


class ChatHistoryItem(BaseModel):
    conversation_id: uuid.UUID
    created_at: datetime
    message_count: int
    latest_message: str


class ConversationHistoryResponse(BaseModel):
    conversation_id: uuid.UUID
    messages: list[ChatMessage]
