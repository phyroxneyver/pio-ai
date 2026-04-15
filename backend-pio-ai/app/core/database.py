from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

# Intenta obtener NEON_URL (Vercel) primero, si no DATABASE_URL, y si no local SQLite
DATABASE_URL = os.getenv("NEON_URL") or os.getenv("DATABASE_URL", "sqlite:////tmp/sql_app.db")

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
