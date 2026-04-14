from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, engine, Base, get_db
from app.core.security import get_password_hash
from app.core.deps import get_current_active_user, require_role

from app.schemas.users import UserCreate, UserResponse
from app.services.users import create_user
from app.models.users import User
from app.models.token_blacklist import TokenBlacklist  # Registrar modelo en metadata

from app.api.auth import router as auth_router

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
    description="Backend para el proyecto Pio AI — Sistema IoT Avícola",
    version="0.2.0",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
@app.on_event("startup")
def startup_db():
    Base.metadata.create_all(bind=engine)

    # Crear usuario admin por defecto si no existe
    db = SessionLocal()
    try:
        admin_email = "admin@pioai.com"
        admin_pass = "123456"
        db_user = db.query(User).filter(User.email == admin_email).first()
        if not db_user:
            hashed_pass = get_password_hash(admin_pass)
            new_user = User(
                email=admin_email,
                hashed_password=hashed_pass,
                role="admin",
                is_active=True,
            )
            db.add(new_user)
            db.commit()
            print("✅ Admin user created successfully")
        else:
            # Asegurar que el admin existente tenga rol admin
            if db_user.role != "admin":
                db_user.role = "admin"
                db.commit()
                print("✅ Admin role updated")
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Rutas públicas
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"message": "Pio AI API is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Usuarios (protegido: solo admin puede registrar nuevos usuarios)
# ---------------------------------------------------------------------------
@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin"))],
)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo usuario. Solo accesible por administradores."""
    return create_user(db=db, user=user)


# ---------------------------------------------------------------------------
# Aves — Rutas protegidas (usuario autenticado y activo)
# ---------------------------------------------------------------------------
@app.post(
    "/aves",
    response_model=AveResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_active_user)],
)
def registrar_ave(ave: AveCreate, db: Session = Depends(get_db)):
    return create_ave(db=db, ave=ave)


@app.get(
    "/aves",
    response_model=list[AveResponse],
    dependencies=[Depends(get_current_active_user)],
)
def listar_aves(db: Session = Depends(get_db)):
    return get_aves(db=db)


@app.put(
    "/aves/{ave_id}",
    response_model=AveResponse,
    dependencies=[Depends(get_current_active_user)],
)
def editar_ave(ave_id: int, datos: AveUpdate, db: Session = Depends(get_db)):
    ave = update_ave(db=db, ave_id=ave_id, datos=datos)
    if not ave:
        raise HTTPException(status_code=404, detail="Ave no encontrada")
    return ave


# ---------------------------------------------------------------------------
# Producción de huevos — Rutas protegidas
# ---------------------------------------------------------------------------
@app.post(
    "/produccion-huevos",
    response_model=ProduccionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(get_current_active_user)],
)
def registrar_produccion(produccion: ProduccionCreate, db: Session = Depends(get_db)):
    ave = db.query(Ave).filter(Ave.id == produccion.ave_id).first()
    if not ave:
        raise HTTPException(status_code=404, detail="Ave no encontrada")
    return create_produccion(db=db, produccion=produccion)


@app.get(
    "/produccion-huevos",
    response_model=list[ProduccionResponse],
    dependencies=[Depends(get_current_active_user)],
)
def listar_produccion(db: Session = Depends(get_db)):
    return get_producciones(db=db)


@app.put(
    "/produccion-huevos/{produccion_id}",
    response_model=ProduccionResponse,
    dependencies=[Depends(get_current_active_user)],
)
def editar_produccion(
    produccion_id: int, datos: ProduccionUpdate, db: Session = Depends(get_db)
):
    prod = update_produccion(db=db, produccion_id=produccion_id, datos=datos)
    if not prod:
        raise HTTPException(
            status_code=404, detail="Registro de producción no encontrado"
        )
    return prod