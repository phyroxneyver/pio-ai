"""
Schemas para tokens JWT y mensajes de respuesta genéricos.
"""
from pydantic import BaseModel
from typing import Optional


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


class MessageResponse(BaseModel):
    """Respuesta genérica para operaciones sin datos de retorno (logout, etc.)."""
    message: str
