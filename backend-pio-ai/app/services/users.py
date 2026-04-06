from sqlalchemy.orm import Session
from app.core.security import get_password_hash
from app.models.users import User
from app.schemas.users import UserCreate

def create_user(db: Session, user: UserCreate) -> User:
    # Lógica central: Encriptamos la contraseña al registrar usuario
    hashed_password = get_password_hash(user.password)
    
    # Creamos el registro en base de datos usando la contraseña hasheada
    db_user = User(
        email=user.email,
        hashed_password=hashed_password
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user
