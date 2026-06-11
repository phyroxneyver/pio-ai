import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.users import create_user
from app.schemas.users import UserCreate
from app.models.users import User

def test_create_user_service(db_session: Session):
    user_data = UserCreate(email="new_user@test.com", password="password123", role="usuario")
    user = create_user(db=db_session, user=user_data)
    
    assert user.id is not None
    assert user.email == "new_user@test.com"
    assert user.role == "usuario"
    assert user.is_active is True
    
    # Verificar que el usuario se guardó en la base de datos
    db_user = db_session.query(User).filter(User.email == "new_user@test.com").first()
    assert db_user is not None
    assert db_user.id == user.id

def test_create_user_duplicate_email(db_session: Session):
    user_data1 = UserCreate(email="dup@test.com", password="password123", role="usuario")
    create_user(db=db_session, user=user_data1)
    
    user_data2 = UserCreate(email="dup@test.com", password="password456", role="admin")
    
    with pytest.raises(HTTPException) as exc_info:
        create_user(db=db_session, user=user_data2)
        
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert "correo ya está registrado" in exc_info.value.detail
