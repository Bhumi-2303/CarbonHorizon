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
from app.services.prompt_templates import (
    build_generation_config,
    build_user_turn,
    INJECTION_DEFLECTION_MESSAGE,
    OUTPUT_VALIDATION_FALLBACK,
    SYSTEM_PROMPT_FRAGMENTS,
)
from app.core.sanitizer import (
    normalize_text,
    validate_length,
    detect_injection,
    validate_output,
    InputTooLongError,
    OutputValidationError,
)

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

Do not apologize or explain further. Return immediately to sustainability topics.
IMPORTANT: Do NOT use emojis in your responses. Your responses must be text-only.

CRITICAL INSTRUCTIONS FOR FORMATTING AND DEMOGRAPHICS:
1. GENDER RELEVANCE: You will be provided with the user's gender. Use this STRICTLY for tone tuning or relevance if applicable, but NEVER let gender gate, restrict, or exclude any recommendations. All recommendations should be available to everyone.
2. LOCALIZED CONTEXT: Leverage the provided city, state, and country to offer highly localized advice (e.g. referencing local transit systems, regional grid mix, local climate, or water scarcity issues).
3. FOOTER TAGS: If your advice relies on specific local context, you MUST append a markdown blockquote at the very end of your response exactly formatted like this:
> **Localized Context:** [City], [State], [Country]
(If you are only given country, just list the country).
4. SUMMARY CARDS: When recommending multiple actionable steps, present them as standard markdown unordered lists (bullet points) so the UI can format them as insight cards."""

CHILD_SYSTEM_PROMPT = """You are the Nature Guide for Little Explorers. You are a friendly, encouraging AI helping kids ages 4-12 learn about nature.

You ONLY answer questions about:
- Helping animals and forests
- Keeping rivers and oceans clean
- Saving energy by turning off lights
- Walking or biking instead of driving
- Recycling and not wasting food or plastic
- Exploring nature

If the child asks about ANYTHING else, respond EXACTLY with:
"I only know about helping nature! Would you like to hear a fun fact about animals or how we can save trees?"

CRITICAL INSTRUCTIONS:
1. Do NOT use emojis.
2. Use extremely simple vocabulary.
3. Tie every tip to a nature outcome (e.g. "Saves the rivers", "Helps the trees grow", "Keeps the air clean for birds").
4. NEVER use the words: CO2, carbon, emissions, footprint, tons, percentages, kWh, or global warming. Use "pollution" or "waste" instead.
5. End every response with one small, easy challenge for the child to do today (e.g. "Can you turn off the water while you brush your teeth tonight?")."""

STUDENT_SYSTEM_PROMPT = """You are the Carbon Horizon Student Coach. You are a relatable, encouraging, and budget-conscious AI helping teenagers (ages 13-17) understand their carbon footprint.

You focus on:
- School/college commutes (bus, bike, carpooling)
- Dorm or bedroom electricity (laptops, AC, leaving lights on)
- Food choices (Meatless Mondays, reducing food waste)
- Sustainable shopping (thrifted clothes, reducing fast fashion)
- Peer-relevant activism and small daily habits

CRITICAL INSTRUCTIONS:
1. Do NOT use emojis.
2. Use a peer-relevant, friendly tone. Avoid dense corporate or enterprise jargon like "Scope 3 emissions", "capital expenditure", or "carbon offsets".
3. YOU CAN use real numbers, percentages, and terms like "CO2", "emissions", and "kWh" to educate them.
4. Keep suggestions budget-friendly or free.
5. Emphasize how small actions make a big collective impact.
6. End with an actionable question or small goal for the week."""

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
    if age_val == 'child' or (user and hasattr(user, 'age') and user.age is not None and user.age <= 12):
        age_str = "Audience: Child (Ages 4-12). Very simple language. Focus on: nature, animals, saving water/electricity."
    elif age_val == 'student' or (user and hasattr(user, 'age') and user.age is not None and user.age <= 17):
        age_str = "Audience: Student. Focus on: daily commute, hostel electricity, food choices, academic travel. Mention budget-friendly sustainability."
    elif age_val == 'adult':
        age_str = "Audience: Adult. Full scope. Emphasize: home energy, vehicle type, family dietary choices, waste systems, long-term goal setting."
    elif age_val in ['senior', 'elderly']:
        age_str = "Audience: Senior/Elderly. Focus on: home energy efficiency, local food sourcing, reduced travel. Simple language. Acknowledge physical limitations."
    else:
        age_str = "Audience: General."

    gender_str = "Unknown"
    if user:
        g = getattr(user, 'gender', None)
        if g:
            gender_str = str(getattr(g, 'value', g))

    lifestyle_str = "Unknown"
    if user:
        ls = getattr(user, 'lifestyle_type', None)
        if ls:
            lifestyle_str = str(getattr(ls, 'value', ls))

    city = getattr(inputs, 'assessment_city', '') if inputs else ""
    if not city and user:
        city = getattr(user, 'city', '')

    state = getattr(inputs, 'assessment_state', '') if inputs else ""
    if not state and user:
        state = getattr(user, 'state_province', '')

    country = getattr(inputs, 'assessment_country', '') if inputs else ""
    if not country and user:
        country = getattr(user, 'country', '')
    
    loc_parts = [p for p in [city, state, country] if p and str(p).strip()]
    if loc_parts:
        loc_str = f"Location: {', '.join(loc_parts)}. Use this specific geographic context to tailor advice (e.g., local weather, local transit, regional grid)."
    else:
        loc_str = "Location: Global. Provide globally applicable advice."

    diet_type = getattr(inputs, 'diet_type', 'Unknown') if inputs else "Unknown"
    transport_mode = getattr(inputs, 'transport_mode', 'Unknown') if inputs else "Unknown"
    total_emission = assessment_dict.get('total_emission', 0) if assessment_dict else 0
    largest_source = get_largest_source(assessment_dict)

    return f"""User context (use this to personalize your response):
- {age_str}
- Gender: {gender_str}
- Occupation/Lifestyle: {lifestyle_str}
- {loc_str}
- Latest annual carbon footprint: {total_emission} tons CO₂e
- Largest emission source: {largest_source}
- Diet: {diet_type}
- Primary transport: {transport_mode}
- Sustainability goals: {goals_context}

CRITICAL: When citing carbon_saved estimates, ALWAYS use the numbers provided in this context or derived directly from it. Never invent or calculate your own raw numbers."""

def chat(db: Session, user_id: uuid.UUID, conversation_id: Optional[uuid.UUID], user_message: str) -> dict:
    import time
    import logging
    from google.genai import errors

    logger = logging.getLogger(__name__)
    security_logger = logging.getLogger("security.prompt_injection")

    # -----------------------------------------------------------------
    # Layer 1 — Input validation & normalization
    # -----------------------------------------------------------------
    # Normalize unicode, strip zero-width chars and control characters
    sanitized_message = normalize_text(user_message)

    # Reject empty messages after normalization
    if not sanitized_message or not sanitized_message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    # Enforce length limit
    try:
        validate_length(sanitized_message)
    except InputTooLongError:
        raise HTTPException(
            status_code=400,
            detail=f"Message is too long. Please keep your message under "
                   f"1000 characters."
        )

    # -----------------------------------------------------------------
    # Layer 2 — Injection detection
    # -----------------------------------------------------------------
    is_injection, category, pattern = detect_injection(
        sanitized_message, user_id=str(user_id)
    )
    if is_injection:
        # Do NOT call Gemini — save cost and return a safe deflection
        security_logger.warning(
            "Coach injection blocked | user_id=%s | category=%s | "
            "action=deflected_without_api_call",
            user_id, category,
        )

        if not conversation_id:
            conversation_id = uuid.uuid4()

        # Still save the user message so conversation history is consistent
        user_conv = AIConversation(
            conversation_id=conversation_id,
            user_id=user_id,
            role=ConversationRole.user,
            message=sanitized_message,
        )
        db.add(user_conv)

        # Save the deflection as the assistant response
        ai_conv = AIConversation(
            conversation_id=conversation_id,
            user_id=user_id,
            role=ConversationRole.assistant,
            message=INJECTION_DEFLECTION_MESSAGE,
        )
        db.add(ai_conv)
        db.commit()

        return {
            "conversation_id": conversation_id,
            "message": INJECTION_DEFLECTION_MESSAGE,
            "ai_message_id": ai_conv.id,
        }

    # -----------------------------------------------------------------
    # Normal flow — everything below is unchanged except for prompt
    # construction (Layer 3) and output validation (Layer 4)
    # -----------------------------------------------------------------

    if not conversation_id:
        conversation_id = uuid.uuid4()
        
    if not settings.GEMINI_API_KEY and not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(status_code=500, detail="Gemini API Key is missing. Please configure it to use the AI Coach.")

    api_key = settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # Save User message (using the sanitized version)
    user_conv = AIConversation(
        conversation_id=conversation_id,
        user_id=user_id,
        role=ConversationRole.user,
        message=sanitized_message,
    )
    db.add(user_conv)
    db.commit()

    # Fetch context
    user = db.get(User, user_id)
    
    assessment_dict = None
    inputs = None
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

    is_child = user and hasattr(user, 'age') and user.age is not None and user.age <= 12
    is_student = user and hasattr(user, 'age') and user.age is not None and user.age >= 13 and user.age <= 17
    
    if is_child:
        prompt_to_use = CHILD_SYSTEM_PROMPT
    elif is_student:
        prompt_to_use = STUDENT_SYSTEM_PROMPT
    else:
        prompt_to_use = SYSTEM_PROMPT

    # -----------------------------------------------------------------
    # Layer 3 — Structural isolation in the Gemini prompt
    # -----------------------------------------------------------------
    # System instruction is set via the API's dedicated parameter (not
    # concatenated with user text).  Anti-injection suffix is appended.
    config = build_generation_config(prompt_to_use)

    # User content is wrapped in <user_message> delimiters with a
    # defensive instruction block.
    coach_context = get_coach_context(user, assessment_dict, inputs, goals_context)
    context_prompt = build_user_turn(sanitized_message, coach_context)

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
            
            # Post-processing filter for kids
            if is_child:
                bad_terms = ["CO2", "carbon footprint", "emissions", "carbon", "kWh"]
                for term in bad_terms:
                    # simple case-insensitive replacement
                    import re
                    ai_text = re.sub(f"(?i){term}", "pollution", ai_text)

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

    # -----------------------------------------------------------------
    # Layer 4 — Output validation
    # -----------------------------------------------------------------
    try:
        validate_output(
            ai_text,
            system_prompt_fragments=SYSTEM_PROMPT_FRAGMENTS,
            user_id=str(user_id),
        )
    except OutputValidationError:
        logger.warning(
            "Output validation failed for user %s — returning fallback",
            user_id,
        )
        ai_text = OUTPUT_VALIDATION_FALLBACK

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
