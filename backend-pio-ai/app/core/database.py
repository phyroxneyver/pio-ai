from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
import pg8000

load_dotenv(override=True)

# --- PARCHE DE EMERGENCIA PARA VERCEL ---
# Interceptamos la función connect para eliminar parámetros conflictivos y FORZAR SSL
original_connect = pg8000.connect
def patched_connect(*args, **kwargs):
    import ssl
    # Eliminamos lo que confunde a pg8000
    kwargs.pop('channel_binding', None)
    kwargs.pop('sslmode', None)
    
    # Forzamos SSL de la manera correcta para pg8000
    if 'ssl_context' not in kwargs:
        kwargs['ssl_context'] = ssl.create_default_context()
        
    return original_connect(*args, **kwargs)
pg8000.connect = patched_connect
# ----------------------------------------

# Intenta obtener de las variables de Vercel (POSTGRES_URL, NEON_URL, o DATABASE_URL)
raw_url = os.getenv("POSTGRES_URL") or os.getenv("NEON_URL") or os.getenv("DATABASE_URL", "sqlite:////tmp/sql_app.db")
if raw_url:
    raw_url = raw_url.strip()
    if raw_url.startswith("postgresql://"):
        raw_url = raw_url.replace("postgresql://", "postgresql+pg8000://", 1)
DATABASE_URL = raw_url if raw_url else "sqlite:////tmp/sql_app.db"

# Ajuste de argumentos según el tipo de base de datos


engine_args = {}
if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    engine_args["connect_args"] = {"check_same_thread": False}



engine = create_engine(DATABASE_URL, **engine_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
