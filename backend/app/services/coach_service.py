import uuid
import os
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
import google.generativeai as genai

from app.core.config import settings
from app.models.ai_conversation import AIConversation
from app.models.goal import Goal
from app.models.habit import Habit
from app.models.enums import GoalStatus, ConversationRole
from app.schemas.coach import ChatMessage
from app.services.assessment_service import AssessmentService

SYSTEM_PROMPT = """You are Carbon Horizon's sustainability coach. You help users understand their carbon footprint and suggest actions. NEVER calculate or modify emission values — all calculations come from our backend engine. Only explain results, provide recommendations, and create action plans."""

def chat(db: Session, user_id: uuid.UUID, conversation_id: uuid.UUID, user_message: str) -> dict:
    if not settings.GEMINI_API_KEY and not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API Key is missing. Please configure it to use the AI Coach.")

    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    genai.configure(api_key=api_key)

    # Save User message
    user_conv = AIConversation(
        conversation_id=conversation_id,
        user_id=user_id,
        role=ConversationRole.user,
        message=user_message,
    )
    db.add(user_conv)
    db.commit()

    # Fetch context
    assessment_data = None
    try:
        assessment = AssessmentService.get_latest_assessment(db, user_id)
        if assessment:
            assessment_data = f"Latest Assessment Total Emissions: {assessment.get('total_emission')} kg CO2e/month"
    except HTTPException:
        assessment_data = "No assessment recorded yet."

    active_goals = db.execute(
        select(Goal).where(Goal.user_id == user_id, Goal.status == GoalStatus.active)
    ).scalars().all()
    goals_context = ", ".join([g.goal_name for g in active_goals]) if active_goals else "No active goals."

    recent_habits = db.execute(
        select(Habit).where(Habit.user_id == user_id).order_by(Habit.activity_date.desc()).limit(10)
    ).scalars().all()
    habits_context = ", ".join([f"{h.habit_type} ({'Done' if h.completed else 'Missed'})" for h in recent_habits]) if recent_habits else "No recent habits logged."

    # Build history
    history = db.execute(
        select(AIConversation)
        .where(AIConversation.conversation_id == conversation_id, AIConversation.id != user_conv.id)
        .order_by(AIConversation.created_at.asc())
    ).scalars().all()

    gemini_history = []
    for msg in history:
        gemini_history.append({
            "role": "model" if msg.role == ConversationRole.assistant else "user",
            "parts": [msg.message],
        })

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT,
    )

    context_prompt = (
        f"[Context - Do not reply to this block directly, use it to inform your answer]\n"
        f"User's Carbon Status: {assessment_data}\n"
        f"User's Active Goals: {goals_context}\n"
        f"User's Recent Habits: {habits_context}\n"
        f"-----------------\n"
        f"{user_message}"
    )

    chat_session = model.start_chat(history=gemini_history)
    response = chat_session.send_message(context_prompt)
    ai_text = response.text

    # Save AI message
    ai_conv = AIConversation(
        conversation_id=conversation_id,
        user_id=user_id,
        role=ConversationRole.assistant,
        message=ai_text,
    )
    db.add(ai_conv)
    db.commit()

    return {
        "conversation_id": conversation_id,
        "message": ai_text,
        "ai_message_id": ai_conv.id
    }

def get_conversation_history(db: Session, user_id: uuid.UUID, conversation_id: uuid.UUID) -> list[ChatMessage]:
    history = db.execute(
        select(AIConversation)
        .where(AIConversation.conversation_id == conversation_id, AIConversation.user_id == user_id)
        .order_by(AIConversation.created_at.asc())
    ).scalars().all()

    return [
        ChatMessage(
            id=msg.id,
            role=msg.role.value if hasattr(msg.role, "value") else msg.role,
            message=msg.message,
            created_at=msg.created_at
        ) for msg in history
    ]
