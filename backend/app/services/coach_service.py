import uuid
import os
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi import HTTPException
from google import genai
from google.genai import types
from typing import Optional

from app.core.config import settings
from app.models.ai_conversation import AIConversation
from app.models.goal import Goal
from app.models.habit import Habit
from app.models.enums import GoalStatus, ConversationRole
from app.schemas.coach import ChatMessage
from app.services.assessment_service import AssessmentService

from app.models.user import User
from app.models.emission_inputs import EmissionInputs

SYSTEM_PROMPT = """You are the Carbon Horizon Sustainability Coach. You are a focused sustainability AI.

You ONLY answer questions about:
- Carbon footprint reduction strategies
- Sustainable transportation
- Renewable energy and home energy efficiency
- Sustainable food and diet choices
- Waste reduction and recycling
- Water conservation
- Eco-friendly lifestyle improvements
- Carbon forecasting and emission reduction
- Climate science education (factual)

If the user asks about ANYTHING else (programming, medicine, law, relationships, homework, general trivia, politics, finance unrelated to sustainability), respond EXACTLY with:
"That falls outside my area of expertise. I'm here to help you understand and reduce your carbon footprint. Is there a sustainability question I can help you with?"

Do not apologize or explain further. Return immediately to sustainability topics."""

def get_largest_source(assessment: dict) -> str:
    if not assessment:
        return "Unknown"
    sources = {
        "Transportation": assessment.get("transport", 0),
        "Energy": assessment.get("energy", 0),
        "Food": assessment.get("food", 0),
        "Waste": assessment.get("waste", 0)
    }
    return max(sources, key=sources.get) if any(sources.values()) else "Unknown"

def get_coach_context(user, assessment_dict, inputs, goals_context) -> str:
    age_val = user.age_group.value if user and hasattr(user.age_group, 'value') else (user.age_group if user else None)
    if age_val == 'child':
        age_str = "Audience: Child. Use simple language. Focus on: school transport, lunch food waste, home electricity habits. Avoid complex carbon finance terms."
    elif age_val == 'student':
        age_str = "Audience: Student. Focus on: daily commute, hostel electricity, food choices, academic travel. Mention budget-friendly sustainability."
    elif age_val == 'adult':
        age_str = "Audience: Adult. Full scope. Emphasize: home energy, vehicle type, family dietary choices, waste systems, long-term goal setting."
    elif age_val in ['senior', 'elderly']:
        age_str = "Audience: Senior/Elderly. Focus on: home energy efficiency, local food sourcing, reduced travel. Simple language. Acknowledge physical limitations."
    else:
        age_str = "Audience: General."

    country = user.country if user else ""
    country_lower = country.lower() if country else ""
    eu_countries = {"germany", "france", "italy", "spain", "netherlands", "belgium", "sweden", "poland", "austria", "ireland", "denmark", "finland", "portugal", "greece", "czech republic"}
    
    if "india" in country_lower:
        loc_str = "Location: India. Mention public transport (metro, buses), solar subsidies, LPG reduction, vegetarian diet advantage."
    elif country_lower in eu_countries:
        loc_str = "Location: EU. Mention carbon offset schemes, EV subsidies, district heating."
    elif country_lower in ["us", "usa", "united states", "america"]:
        loc_str = "Location: US. Mention EV tax credits, home insulation programs, recycling variability by state."
    else:
        loc_str = "Location: Global. Provide globally applicable advice."

    diet_type = inputs.diet_type if inputs else "Unknown"
    transport_mode = inputs.transport_mode if inputs else "Unknown"
    total_emission = assessment_dict.get('total_emission', 0) if assessment_dict else 0
    largest_source = get_largest_source(assessment_dict)

    return f"""User context (use this to personalize your response):
- {age_str}
- {loc_str}
- Latest annual carbon footprint: {total_emission} tons CO₂e
- Largest emission source: {largest_source}
- Diet: {diet_type}
- Primary transport: {transport_mode}
- Sustainability goals: {goals_context}

CRITICAL: When citing carbon_saved estimates, ALWAYS use the numbers provided in this context or derived directly from it. Never invent or calculate your own raw numbers."""

def chat(db: Session, user_id: uuid.UUID, conversation_id: Optional[uuid.UUID], user_message: str) -> dict:
    if not conversation_id:
        conversation_id = uuid.uuid4()
        
    if not settings.GEMINI_API_KEY and not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API Key is missing. Please configure it to use the AI Coach.")

    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

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
    user = db.get(User, user_id)
    
    assessment_dict = None
    diet_type = "Unknown"
    transport_mode = "Unknown"
    try:
        assessment_dict = AssessmentService.get_latest_assessment(db, user_id)
        if assessment_dict:
            latest_id = assessment_dict.get("assessment_id")
            inputs = db.execute(select(EmissionInputs).where(EmissionInputs.assessment_id == latest_id)).scalars().first()
            if inputs:
                diet_type = inputs.diet_type
                transport_mode = inputs.transport_mode
    except HTTPException:
        pass

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
        role = "model" if msg.role == ConversationRole.assistant else "user"
        gemini_history.append(
            types.Content(role=role, parts=[types.Part.from_text(text=msg.message)])
        )

    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
    )

    context_prompt = (
        f"{get_coach_context(user, assessment_dict, inputs, goals_context)}\n\n"
        f"User Message: {user_message}"
    )

    import time
    import logging
    from google.genai import errors
    
    logger = logging.getLogger(__name__)

    MAX_RETRIES = 3
    RETRY_DELAYS = [0, 2, 5]
    RETRYABLE_CODES = {429, 500, 502, 503, 504}
    
    current_model = "gemini-2.5-flash"
    fallback_model = "gemini-2.0-flash"
    ai_text = None
    
    for attempt in range(MAX_RETRIES):
        if attempt > 0:
            time.sleep(RETRY_DELAYS[attempt])
            
        start_time = time.time()
        try:
            chat_session = client.chats.create(model=current_model, config=config, history=gemini_history)
            response = chat_session.send_message(context_prompt)
            ai_text = response.text
            latency_ms = int((time.time() - start_time) * 1000)
            logger.info(f"AI Coach success. Model: {current_model}, Latency: {latency_ms}ms, Retry count: {attempt}")
            break
            
        except errors.APIError as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.warning(f"AI Coach APIError. Model: {current_model}, Latency: {latency_ms}ms, Attempt: {attempt + 1}, Code: {e.code}, Message: {e.message}")
            
            if e.code not in RETRYABLE_CODES:
                logger.error(f"Non-retryable Gemini error: {e.code}")
                raise HTTPException(status_code=503, detail="The AI Coach is temporarily unavailable.")
                
            if e.code == 503 and current_model != fallback_model:
                logger.info(f"Fallback triggered. Switching model from {current_model} to {fallback_model}")
                current_model = fallback_model
                
            if attempt == MAX_RETRIES - 1:
                logger.error(f"Max retries exhausted for AI Coach.")
                if e.code == 503:
                    raise HTTPException(status_code=503, detail="The AI Coach is currently busy. Please try again in a few moments.")
                elif e.code == 429:
                    raise HTTPException(status_code=429, detail="The AI Coach is experiencing high demand. Please try again shortly.")
                elif e.code == 504:
                    raise HTTPException(status_code=504, detail="The AI Coach took too long to respond. Please try again.")
                else:
                    raise HTTPException(status_code=503, detail="The AI Coach is temporarily unavailable.")
                    
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            logger.exception(f"AI Coach unexpected error. Model: {current_model}, Latency: {latency_ms}ms, Attempt: {attempt + 1}")
            if attempt == MAX_RETRIES - 1:
                raise HTTPException(status_code=500, detail="The AI Coach is temporarily unavailable.")
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
