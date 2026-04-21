import sys
import os
from dotenv import load_dotenv

# Cargar variables de .env.local (donde vercel env pull descargó los secretos)
load_dotenv(".env.local")

# Asegurar que el directorio actual esté en el path
sys.path.append(os.path.dirname(__file__))

# Importar lo necesario del proyecto
from app.core.database import SessionLocal, engine, Base
from app.services.users import create_user
from app.schemas.users import UserCreate
from app.models.users import User

def add_admin():
    print("Conectando a la base de datos...")
    # Crear tablas si no existen (en caso de que Neon esté vacío)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        user_data = UserCreate(
            email="admin@pioai.com",
            password="123456",
            role="admin"
        )
        
        # Verificar si ya existe para no duplicar
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            print(f"El usuario {user_data.email} ya existe. Saltando creación.")
        else:
            create_user(db, user_data)
            print(f"✅ Usuario {user_data.email} creado exitosamente como admin.")
    except Exception as e:
        print(f"❌ Error al crear usuario: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    add_admin()
