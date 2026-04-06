from passlib.context import CryptContext

# Creamos el contexto indicando que usaremos bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Toma una contraseña en texto plano y devuelve el hash seguro."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica si la contraseña en texto plano coincide con el hash de la DB."""
    return pwd_context.verify(plain_password, hashed_password)
