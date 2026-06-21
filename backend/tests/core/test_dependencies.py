import pytest
from fastapi import HTTPException
from app.core.dependencies import get_db, get_current_user
from unittest.mock import patch
from app.core.security import JWTError

def test_get_db():
    gen = get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass

@patch("app.core.dependencies.decode_token")
def test_get_current_user(mock_decode):
    mock_decode.return_value = {"sub": "1"}
    user = get_current_user("token", None)
    assert user["id"] == 1
    
    mock_decode.return_value = {}
    with pytest.raises(HTTPException) as exc:
        get_current_user("token", None)
    assert exc.value.status_code == 401
    
    mock_decode.side_effect = JWTError("invalid")
    with pytest.raises(HTTPException) as exc:
        get_current_user("token", None)
    assert exc.value.status_code == 401
