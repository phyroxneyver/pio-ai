"""
Servicio de usuarios.
Contiene la lógica de negocio para creación y gestión de usuarios.
"""
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.core.security import get_password_hash
from app.models.users import User
from app.schemas.users import UserCreate


def create_user(db: Session, user: UserCreate) -> User:
    """
    Crea un nuevo usuario con contraseña hasheada y rol asignado.
    Valida que el email no esté duplicado.
    """
    # Verificar duplicado
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado",
        )

    hashed_password = get_password_hash(user.password)

    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        role=user.role,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user
