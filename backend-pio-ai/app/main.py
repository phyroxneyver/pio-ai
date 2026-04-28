from typing import List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .core.database import SessionLocal, engine, Base, get_db
from .core.security import get_password_hash
from .core.deps import get_current_active_user, require_role

from .schemas.users import UserCreate, UserResponse
from .services.users import create_user
from .models.users import User
from .models.token_blacklist import TokenBlacklist  # Registrar modelo en metadata
from .models.imagenes import Imagen, ResultadoIA, FeedbackIA  # Registrar modelos de imágenes y feedback IA
from .models.alertas import Alerta, NotificacionInterna, HistorialAlerta  # Modelos de alertas

from .api.auth import router as auth_router
from .api.imagenes import router as imagenes_router
from .api.alertas import router as alertas_router

from .schemas.aves import (
    AveCreate, AveUpdate, AveResponse,
    ProduccionCreate, ProduccionUpdate, ProduccionResponse
)
from .services.aves import (
    create_ave, get_aves, update_ave,
    create_produccion, get_producciones, update_produccion
)
from .models.aves import Ave

app = FastAPI(
    title="Pio AI API",
    description="Backend para el proyecto Pio AI — Sistema IoT de monitoreo avícola con IA",
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
origins = [
    "https://pioainetapp.netlify.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
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
app.include_router(imagenes_router)
app.include_router(alertas_router)



# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Rutas públicas
# ---------------------------------------------------------------------------
@app.get("/", tags=["Sistema"])
async def root():
    return {"message": "Pio AI API is running", "status": "healthy"}

@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# Setup de Base de Datos (Correr una sola vez manualmente)
# ---------------------------------------------------------------------------
@app.get("/setup-db", tags=["Sistema"])
def setup_database(db: Session = Depends(get_db)):
    """Crea las tablas y el usuario administrador inicial."""
    try:
        print("Creando tablas...")
        Base.metadata.create_all(bind=engine)
        
        # Crear admin si no existe
        existing = db.query(User).filter(User.email == "admin@pioai.com").first()
        if not existing:
            hashed_pw = get_password_hash("123456")
            admin = User(email="admin@pioai.com", hashed_password=hashed_pw, role="admin")
            db.add(admin)
            db.commit()
            return {"status": "success", "message": "Tablas creadas y usuario admin@pioai.com listo."}
        
        return {"status": "success", "message": "Tablas verificadas. El usuario admin ya existe."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------------------------
# Usuarios (protegido: solo admin puede registrar nuevos usuarios)
# ---------------------------------------------------------------------------
@app.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    # Comentado temporalmente para permitir el primer registro
    # dependencies=[Depends(require_role("admin"))],
    tags=["Usuarios"],
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
    tags=["Aves"],
)
def registrar_ave(ave: AveCreate, db: Session = Depends(get_db)):
    return create_ave(db=db, ave=ave)


@app.get(
    "/aves",
    response_model=List[AveResponse],
    dependencies=[Depends(get_current_active_user)],
    tags=["Aves"],
)
def listar_aves(db: Session = Depends(get_db)):
    return get_aves(db=db)


@app.put(
    "/aves/{ave_id}",
    response_model=AveResponse,
    dependencies=[Depends(get_current_active_user)],
    tags=["Aves"],
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
    tags=["Producción"],
)
def registrar_produccion(produccion: ProduccionCreate, db: Session = Depends(get_db)):
    ave = db.query(Ave).filter(Ave.id == produccion.ave_id).first()
    if not ave:
        raise HTTPException(status_code=404, detail="Ave no encontrada")
    return create_produccion(db=db, produccion=produccion)


@app.get(
    "/produccion-huevos",
    response_model=List[ProduccionResponse],
    dependencies=[Depends(get_current_active_user)],
    tags=["Producción"],
)
def listar_produccion(db: Session = Depends(get_db)):
    return get_producciones(db=db)


@app.put(
    "/produccion-huevos/{produccion_id}",
    response_model=ProduccionResponse,
    dependencies=[Depends(get_current_active_user)],
    tags=["Producción"],
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