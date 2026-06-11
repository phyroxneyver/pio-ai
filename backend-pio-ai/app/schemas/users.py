"""
Schemas de usuario con soporte de roles.
"""
from pydantic import BaseModel, ConfigDict, EmailStr, field_validator
from typing import Optional

VALID_ROLES = ("admin", "usuario")


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "usuario"

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("La contraseña debe tener al menos 6 caracteres")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        if v not in VALID_ROLES:
            raise ValueError(f"Rol inválido. Roles permitidos: {VALID_ROLES}")
        return v


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
