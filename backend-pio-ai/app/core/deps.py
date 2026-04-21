from typing import Optional
"""
Dependencias de seguridad (middleware) para FastAPI.

Provee funciones reutilizables como Depends() para:
- Validación de token JWT
- Verificación de usuario activo
- Control de acceso por roles
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from .database import get_db
from .security import SECRET_KEY, ALGORITHM
from ..models.users import User
from ..services.auth import is_token_blacklisted

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# ---------------------------------------------------------------------------
# Dependency: obtener usuario actual a partir del token
# ---------------------------------------------------------------------------
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Middleware principal de validación de token.
    1. Decodifica el JWT
    2. Verifica que el token no esté en la blacklist
    3. Busca el usuario en la BD
    4. Retorna el usuario autenticado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # --- Decodificar token ---
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # --- Verificar blacklist (token revocado por logout) ---
    if is_token_blacklisted(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revocado. Inicie sesión nuevamente.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # --- Buscar usuario en BD ---
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    return user


# ---------------------------------------------------------------------------
# Dependency: usuario activo
# ---------------------------------------------------------------------------
async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Verifica que el usuario esté activo (no deshabilitado)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario deshabilitado",
        )
    return current_user


# ---------------------------------------------------------------------------
# Dependency factory: requerir rol específico
# ---------------------------------------------------------------------------
def require_role(*allowed_roles: str):
    """
    Factory de dependencias para restringir acceso por rol.

    Uso:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        def admin_endpoint(): ...

        @router.get("/multi", dependencies=[Depends(require_role("admin", "usuario"))])
        def multi_role_endpoint(): ...
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Acceso denegado. Roles permitidos: {', '.join(allowed_roles)}",
            )
        return current_user

    return role_checker
