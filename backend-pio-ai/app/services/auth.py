"""
Servicio de autenticación.
Maneja la blacklist de tokens y la validación de sesiones.
"""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from ..models.token_blacklist import TokenBlacklist
from ..core.security import SECRET_KEY, ALGORITHM


def blacklist_token(db: Session, token: str) -> None:
    """
    Agrega un token a la blacklist para invalidarlo.
    Extrae la fecha de expiración del propio token.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            expires_at = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
        else:
            expires_at = datetime.now(timezone.utc)
    except JWTError:
        expires_at = datetime.now(timezone.utc)

    entry = TokenBlacklist(
        token=token,
        expires_at=expires_at,
    )
    db.add(entry)
    db.commit()


def is_token_blacklisted(db: Session, token: str) -> bool:
    """Verifica si un token está en la blacklist."""
    return (
        db.query(TokenBlacklist)
        .filter(TokenBlacklist.token == token)
        .first()
        is not None
    )


def cleanup_expired_tokens(db: Session) -> int:
    """
    Elimina tokens expirados de la blacklist para mantener la tabla limpia.
    Retorna la cantidad de registros eliminados.
    """
    now = datetime.now(timezone.utc)
    deleted = (
        db.query(TokenBlacklist)
        .filter(TokenBlacklist.expires_at < now)
        .delete()
    )
    db.commit()
    return deleted
