import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.session import Base
from app.models.user import User
from app.models.enums import LifestyleType, Gender
from app.services.coach_service import chat
import uuid

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

u = User(id=uuid.uuid4(), email="test@test.com", password_hash="hash", username="test", lifestyle_type=LifestyleType.professional, gender=Gender.female)
db.add(u)
db.commit()

try:
    chat(db, u.id, None, "Hello")
except Exception as e:
    import traceback
    traceback.print_exc()

