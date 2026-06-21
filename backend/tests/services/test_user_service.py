import pytest
import uuid
from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate
from app.models.user import User

def test_user_service_crud(db):
    # Create
    user_payload = UserCreate(
        email="test_user_service@example.com",
        password="securepassword",
        full_name="Test User",
        age=30,
        gender="Male",
        country="USA",
        state_province="CA",
        city="SF",
        age_group="adult",
        lifestyle_type="professional"
    )
    user = UserService.create(db, user_payload)
    
    assert user.id is not None
    assert user.email == "test_user_service@example.com"
    assert user.full_name == "Test User"
    
    # Read by ID
    fetched_user = UserService.get_by_id(db, user.id)
    assert fetched_user is not None
    assert fetched_user.id == user.id
    
    # Read by Email
    fetched_email = UserService.get_by_email(db, "test_user_service@example.com")
    assert fetched_email is not None
    assert fetched_email.id == user.id
    
    # Update
    update_payload = UserUpdate(full_name="Updated Name")
    updated_user = UserService.update(db, user, update_payload)
    assert updated_user.full_name == "Updated Name"
    
    # List
    users_list = UserService.list_users(db, limit=10000)
    assert len(users_list) > 0
    assert any(u.email == "test_user_service@example.com" for u in users_list)
    
    # Delete
    UserService.delete(db, user)
    assert UserService.get_by_id(db, user.id) is None
