import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash, create_access_token
from app.models.users import User
from app.core.ml import ml_models

# Configurar motor de base de datos SQLite en memoria para pruebas
SQLALCHEMY_DATABASE_URL = "sqlite://"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function", autouse=True)
def setup_ml_model():
    """Asegura que el modelo mock de YOLO esté cargado antes de cada prueba."""
    ml_models["yolo"] = "YOLO_MODEL_LOADED"
    yield
    ml_models.clear()

@pytest.fixture(scope="function")
def db_session():
    """Crea una base de datos limpia para cada caso de prueba y la destruye después."""
    Base.metadata.create_all(bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Retorna un TestClient de FastAPI con la dependencia de BD anulada."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
            
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def test_admin_user(db_session):
    """Crea y retorna un usuario administrador en la base de datos."""
    hashed_pw = get_password_hash("admin123")
    user = User(
        email="admin@test.com",
        hashed_password=hashed_pw,
        role="admin",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def test_regular_user(db_session):
    """Crea y retorna un usuario regular en la base de datos."""
    hashed_pw = get_password_hash("user123")
    user = User(
        email="user@test.com",
        hashed_password=hashed_pw,
        role="usuario",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture(scope="function")
def admin_headers(test_admin_user):
    """Retorna las cabeceras de autorización de Bearer Token para el admin."""
    token = create_access_token(data={"sub": test_admin_user.email, "role": test_admin_user.role})
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture(scope="function")
def user_headers(test_regular_user):
    """Retorna las cabeceras de autorización de Bearer Token para un usuario regular."""
    token = create_access_token(data={"sub": test_regular_user.email, "role": test_regular_user.role})
    return {"Authorization": f"Bearer {token}"}
