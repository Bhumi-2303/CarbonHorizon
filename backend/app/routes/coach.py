import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.security import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import APIResponse
from app.schemas.coach import (
    ChatRequest,
    ChatResponse,
    ConversationHistoryResponse,
)
from app.services import coach_service
from app.core.rate_limit import limiter
from app.core.client_ip import get_trusted_client_ip
from app.core.turnstile import verify_turnstile_token

router = APIRouter()


@router.post(
    "/chat",
    response_model=APIResponse[ChatResponse],
    status_code=status.HTTP_200_OK,
)
@limiter.limit("20/minute")
async def chat_with_coach(
    request: Request,
    payload: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message to the AI Sustainability Coach.
    """
    client_ip = get_trusted_client_ip(request)
    await verify_turnstile_token(payload.turnstile_token, remote_ip=client_ip)
    try:
        response_data = coach_service.chat(
            db=db,
            user_id=current_user.id,
            conversation_id=payload.conversation_id,
            user_message=payload.message,
        )
        return APIResponse(success=True, data=ChatResponse(**response_data))
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error in chat_with_coach: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An internal server error occurred."
        )


@router.get(
    "/history", response_model=APIResponse[ConversationHistoryResponse]
)
@limiter.limit("60/minute")
def get_chat_history(
    request: Request,
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the full chat history for a specific conversation session.
    """
    messages = coach_service.get_conversation_history(
        db=db, user_id=current_user.id, conversation_id=conversation_id
    )

    return APIResponse(
        success=True,
        data=ConversationHistoryResponse(
            conversation_id=conversation_id, messages=messages
        ),
    )
