from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base, get_db
from app.schemas.users import UserCreate, UserResponse
from app.services.users import create_user
from app.models.users import User
from app.api.auth import router as auth_router
from app.core.security import get_password_hash

from app.schemas.aves import (
    AveCreate, AveUpdate, AveResponse,
    ProduccionCreate, ProduccionUpdate, ProduccionResponse
)
from app.services.aves import (
    create_ave, get_aves, update_ave,
    create_produccion, get_producciones, update_produccion
)
from app.models.aves import Ave

app = FastAPI(
    title="Pio AI API",
    description="Backend para el proyecto Pio AI",
    version="0.1.4"
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



@app.get("/")
async def root():
    return {"message": "Pio AI API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

#Usuarios 

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El correo ya está registrado")
    return create_user(db=db, user=user)

# Aves (pollitos / gallinas)

@app.post("/aves", response_model=AveResponse, status_code=status.HTTP_201_CREATED)
def registrar_ave(ave: AveCreate, db: Session = Depends(get_db)):
    
    return create_ave(db=db, ave=ave)

@app.get("/aves", response_model=list[AveResponse])
def listar_aves(db: Session = Depends(get_db)):
    
    return get_aves(db=db)

@app.put("/aves/{ave_id}", response_model=AveResponse)
def editar_ave(ave_id: int, datos: AveUpdate, db: Session = Depends(get_db)):
    
    ave = update_ave(db=db, ave_id=ave_id, datos=datos)
    if not ave:
        raise HTTPException(status_code=404, detail="Ave no encontrada")
    return ave

#Producción de huevos 

@app.post("/produccion-huevos", response_model=ProduccionResponse, status_code=status.HTTP_201_CREATED)
def registrar_produccion(produccion: ProduccionCreate, db: Session = Depends(get_db)):
   
    ave = db.query(Ave).filter(Ave.id == produccion.ave_id).first()
    if not ave:
        raise HTTPException(status_code=404, detail="Ave no encontrada")
    return create_produccion(db=db, produccion=produccion)

@app.get("/produccion-huevos", response_model=list[ProduccionResponse])
def listar_produccion(db: Session = Depends(get_db)):
    
    return get_producciones(db=db)

@app.put("/produccion-huevos/{produccion_id}", response_model=ProduccionResponse)
def editar_produccion(produccion_id: int, datos: ProduccionUpdate, db: Session = Depends(get_db)):
    
    prod = update_produccion(db=db, produccion_id=produccion_id, datos=datos)
    if not prod:
        raise HTTPException(status_code=404, detail="Registro de producción no encontrado")
    return prod