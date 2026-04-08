from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base, get_db
from app.schemas.users import UserCreate, UserResponse
from app.services.users import create_user
from app.models.users import User
from app.api.auth import router as auth_router
from app.core.security import get_password_hash

app = FastAPI(
    title="Pio AI API",
    description="Backend para el proyecto Pio AI",
    version="0.1.2"
)

# CORS
origins = [
    "https://pioainetapp.netlify.app/",
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

# Routers
app.include_router(auth_router)

# Inicializar tablas al arrancar y asegurar usuario admin
@app.on_event("startup")
def startup_db():
    Base.metadata.create_all(bind=engine)
    
    # Crear usuario por defecto si no existe
    db = SessionLocal()
    try:
        admin_email = "admin@pioai.com"
        admin_pass = "123456"
        db_user = db.query(User).filter(User.email == admin_email).first()
        if not db_user:
            hashed_pass = get_password_hash(admin_pass)
            new_user = User(email=admin_email, hashed_password=hashed_pass)
            db.add(new_user)
            db.commit()
            print("Admin user created successfully")
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
