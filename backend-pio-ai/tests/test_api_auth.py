import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.users import User
from app.core.security import get_password_hash

def test_api_register_user(client: TestClient):
    response = client.post(
        "/register",
        json={"email": "new_api_user@test.com", "password": "password123", "role": "usuario"}
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "new_api_user@test.com"
    assert data["role"] == "usuario"
    assert data["is_active"] is True
    assert "id" in data

def test_api_login_success(client: TestClient, db_session: Session):
    # Crear un usuario de prueba
    hashed_pw = get_password_hash("password123")
    user = User(email="login_user@test.com", hashed_password=hashed_pw, role="usuario", is_active=True)
    db_session.add(user)
    db_session.commit()
    
    # Intentar login
    response = client.post(
        "/auth/login",
        data={"username": "login_user@test.com", "password": "password123"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_api_login_failure(client: TestClient):
    response = client.post(
        "/auth/login",
        data={"username": "non_existent@test.com", "password": "wrong_password"}
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "incorrectos" in response.json()["detail"]

def test_api_login_disabled_user(client: TestClient, db_session: Session):
    hashed_pw = get_password_hash("password123")
    user = User(email="disabled@test.com", hashed_password=hashed_pw, role="usuario", is_active=False)
    db_session.add(user)
    db_session.commit()
    
    response = client.post(
        "/auth/login",
        data={"username": "disabled@test.com", "password": "password123"}
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "deshabilitada" in response.json()["detail"]

def test_api_read_users_me(client: TestClient, user_headers):
    response = client.get("/auth/me", headers=user_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "user@test.com"
    assert data["role"] == "usuario"

def test_api_logout_invalidates_token(client: TestClient, user_headers):
    # El primer logout debe funcionar
    response = client.post("/auth/logout", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    assert "exitosamente" in response.json()["message"]
    
    # El segundo intento con el mismo token debe fallar por estar en la blacklist
    response2 = client.get("/auth/me", headers=user_headers)
    assert response2.status_code == status.HTTP_401_UNAUTHORIZED
