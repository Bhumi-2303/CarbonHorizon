import uuid
import os
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.enums import AgeGroup, LifestyleType, Gender
from app.services.coach_service import get_coach_context
from google.genai import types

# Use dummy sqlite memory for the test
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# Create test user
user_id = uuid.uuid4()
u = User(
    id=user_id,
    full_name="Bhumi Patel",
    email="bhumi@example.com",
    password_hash="hash",
    age_group=AgeGroup.adult,
    lifestyle_type=LifestyleType.student,  # student but >18
    age=20,
    gender=Gender.female,
    country="India",
    state_province="Gujarat",
    city="Surat"
)
db.add(u)
db.commit()

print("==== CONTEXT GENERATED FOR PROMPT ====")
try:
    ctx = get_coach_context(u, None, None, "No active goals.")
    print(ctx)
except Exception as e:
    import traceback
    traceback.print_exc()

