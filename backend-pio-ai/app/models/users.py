"""
Modelo de usuario con soporte de roles.
Roles disponibles: 'admin', 'usuario'
"""
from sqlalchemy import Column, Integer, String, Boolean
from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="usuario")
    is_active = Column(Boolean, default=True, nullable=False)
