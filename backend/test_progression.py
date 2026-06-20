import uuid
import sys

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User
from app.models.carbon_assessment import CarbonAssessment
from app.models.enums import AgeGroup, LifestyleType, Gender
from app.services.progression_service import ProgressionService
import datetime

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
    lifestyle_type=LifestyleType.student,
    age=20,
    gender=Gender.female,
)
db.add(u)
db.commit()

# Add assessments to test emission reduction
ca1 = CarbonAssessment(user_id=user_id, total_emission=10.0, created_at=datetime.datetime(2025, 1, 1))
ca2 = CarbonAssessment(user_id=user_id, total_emission=8.5, created_at=datetime.datetime(2025, 6, 1))
db.add(ca1)
db.add(ca2)
db.commit()

print("==== PROGRESSION DATA ====")
try:
    prog = ProgressionService.calculate_progression(db, user_id)
    print(prog)
except Exception as e:
    import traceback
    traceback.print_exc()

