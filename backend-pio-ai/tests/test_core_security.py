import pytest
from datetime import timedelta
from jose import jwt

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    SECRET_KEY,
    ALGORITHM
)

def test_password_hashing():
    password = "secret_password"
    hashed = get_password_hash(password)
    
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong_password", hashed) is False

def test_create_access_token():
    data = {"sub": "user@test.com", "role": "usuario"}
    token = create_access_token(data=data)
    
    assert isinstance(token, str)
    
    # Decodificar el token para validar su contenido
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload.get("sub") == "user@test.com"
    assert payload.get("role") == "usuario"
    assert "exp" in payload

def test_create_access_token_with_expires():
    data = {"sub": "admin@test.com", "role": "admin"}
    expires = timedelta(minutes=10)
    token = create_access_token(data=data, expires_delta=expires)
    
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert payload.get("sub") == "admin@test.com"
    assert payload.get("role") == "admin"
    assert "exp" in payload
