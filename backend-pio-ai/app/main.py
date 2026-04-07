from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import os

# Importaciones relativas abackend-pio-ai/
from app.core.database import SessionLocal, engine, Base
from app.schemas.users import UserCreate, UserResponse
from app.services.users import create_user
from app.models.users import User

# Inicialización de base de datos
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pio AI API",
    description="Backend para el proyecto Pio AI implementado para Vercel",
    version="0.1.2"
)

# Configuración de CORS
origins = [
    "https://tu-app-en-netlify.netlify.app",
    "http://localhost:3000",                
    "http://localhost:5173",                
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependencia de DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Rutas
@app.get("/")
async def root():
    return {"message": "Pio AI API is running on Vercel", "status": "healthy"}

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return create_user(db=db, user=user)

@app.get("/health")
async def health_check():
    return {"status": "ok"}
