import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.services.auth import blacklist_token, is_token_blacklisted, cleanup_expired_tokens
from app.core.security import create_access_token
from app.models.token_blacklist import TokenBlacklist

def test_blacklist_token(db_session: Session):
    token = create_access_token(data={"sub": "user@test.com"})
    
    assert is_token_blacklisted(db_session, token) is False
    
    blacklist_token(db_session, token)
    
    assert is_token_blacklisted(db_session, token) is True

def test_cleanup_expired_tokens(db_session: Session):
    # Crear un token ya expirado (con delta negativo)
    expired_token = create_access_token(data={"sub": "expired@test.com"}, expires_delta=timedelta(minutes=-10))
    # Crear un token activo
    active_token = create_access_token(data={"sub": "active@test.com"}, expires_delta=timedelta(minutes=10))
    
    # Blacklistear ambos
    blacklist_token(db_session, expired_token)
    blacklist_token(db_session, active_token)
    
    assert is_token_blacklisted(db_session, expired_token) is True
    assert is_token_blacklisted(db_session, active_token) is True
    
    # Ejecutar la limpieza
    deleted_count = cleanup_expired_tokens(db_session)
    
    assert deleted_count == 1
    assert is_token_blacklisted(db_session, expired_token) is False
    assert is_token_blacklisted(db_session, active_token) is True
