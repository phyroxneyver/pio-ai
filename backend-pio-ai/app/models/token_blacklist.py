"""
Modelo para la blacklist de tokens JWT.
Cuando un usuario hace logout, su token se registra aquí
para impedir su reutilización hasta que expire naturalmente.
"""
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone
from ..core.database import Base


class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, index=True, nullable=False)
    blacklisted_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)
