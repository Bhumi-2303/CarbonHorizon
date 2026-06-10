"""
Coach router  —  /api/coach

Endpoints
---------
POST /api/coach/chat               Send a user message; get AI response
GET  /api/coach/conversations      List all conversation sessions for the user
GET  /api/coach/conversations/{conversation_id}
                                   Fetch all messages in a conversation session
DELETE /api/coach/conversations/{conversation_id}
                                   Delete a conversation session and all its messages

All endpoints return {"detail": "not implemented"} until services are wired.
"""
from fastapi import APIRouter, status
from uuid import UUID

router = APIRouter()

_NOT_IMPLEMENTED = {"detail": "not implemented"}


@router.post(
    "/chat",
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to the AI coach and receive a response",
)
async def chat():
    return _NOT_IMPLEMENTED


@router.get(
    "/conversations",
    summary="List all AI coach conversation sessions for the current user",
)
async def list_conversations():
    return _NOT_IMPLEMENTED


@router.get(
    "/conversations/{conversation_id}",
    summary="Fetch all messages in a specific conversation session",
)
async def get_conversation(conversation_id: UUID):
    return _NOT_IMPLEMENTED


@router.delete(
    "/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a conversation session and all its messages",
)
async def delete_conversation(conversation_id: UUID):
    return _NOT_IMPLEMENTED
