import sys
import os

# add backend to path
sys.path.insert(0, os.path.abspath("."))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.schemas.auth import RegisterRequest, LoginRequest
from app.services.auth_service import register_user, login_user

engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

payload = RegisterRequest(
    full_name="Test User",
    email="test@example.com",
    password="password123"
)

try:
    reg_resp = register_user(db, payload)
    print("Registered successfully.")
except Exception as e:
    print(f"Register failed: {e}")

try:
    login_user(db, "test@example.com", "password123")
    print("Login successfully.")
except Exception as e:
    print(f"Login failed: {e}")
