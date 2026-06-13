from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import uuid

from app.core.security import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import APIResponse
from app.schemas.coach import ChatRequest, ChatResponse, ConversationHistoryResponse
from app.services import coach_service

router = APIRouter()

@router.post("/chat", response_model=APIResponse[ChatResponse], status_code=status.HTTP_200_OK)
def chat_with_coach(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Send a message to the AI Sustainability Coach.
    Returns the AI's response along with context injected automatically.
    """
    try:
        response_data = coach_service.chat(
            db=db,
            user_id=current_user.id,
            conversation_id=request.conversation_id,
            user_message=request.message
        )
        return APIResponse(success=True, data=ChatResponse(**response_data))
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=APIResponse[ConversationHistoryResponse])
def get_chat_history(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the full chat history for a specific conversation session.
    """
    messages = coach_service.get_conversation_history(
        db=db,
        user_id=current_user.id,
        conversation_id=conversation_id
    )
    
    return APIResponse(
        success=True,
        data=ConversationHistoryResponse(
            conversation_id=conversation_id,
            messages=messages
        )
    )
