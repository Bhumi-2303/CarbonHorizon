import pytest
from app.services.user_service import UserService

def test_user_service_stubs(db):
    with pytest.raises(NotImplementedError):
        UserService.get_by_id(db, 1)
    
    with pytest.raises(NotImplementedError):
        UserService.get_by_email(db, "test@test.com")
        
    with pytest.raises(NotImplementedError):
        UserService.list_users(db)
        
    with pytest.raises(NotImplementedError):
        UserService.create(db, None)
        
    with pytest.raises(NotImplementedError):
        UserService.update(db, None, None)
        
    with pytest.raises(NotImplementedError):
        UserService.delete(db, None)
