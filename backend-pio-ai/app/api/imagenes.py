"""
Router de imágenes — Endpoints protegidos para gestión de imágenes avícolas.

Endpoints:
  POST   /imagenes/upload       → Subir una imagen
  GET    /imagenes               → Listar imágenes (paginado)
  GET    /imagenes/{imagen_id}   → Detalle de una imagen
  DELETE /imagenes/{imagen_id}   → Eliminar imagen (solo admin)
  POST   /imagenes/cleanup       → Limpieza de archivos temporales (solo admin)
"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.deps import get_current_active_user, require_role
from ..models.users import User
from ..schemas.imagenes import (
    ImagenDeleteResponse,
    ImagenListResponse,
    ImagenResponse,
)
from ..services.imagenes import (
    cleanup_temp_files,
    delete_imagen,
    get_imagen_by_id,
    get_imagenes,
    upload_imagen,
)

router = APIRouter(prefix="/imagenes", tags=["Imágenes"])


# ---------------------------------------------------------------------------
# POST /imagenes/upload — Subir una imagen
# ---------------------------------------------------------------------------
@router.post(
    "/upload",
    response_model=ImagenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir una imagen para análisis",
)
async def subir_imagen(
    file: UploadFile = File(
        ...,
        description="Archivo de imagen (JPG o PNG, máx. 10 MB)",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Sube una imagen al sistema.

    - Valida tipo de archivo (solo JPG/PNG)
    - Genera nombre único (UUID)
    - Detecta duplicados por hash SHA-256
    - Crea registro de ResultadoIA en estado 'pendiente'
    """
    imagen = await upload_imagen(
        db=db,
        file=file,
        usuario_id=current_user.id,
    )
    return imagen


# ---------------------------------------------------------------------------
# GET /imagenes — Listar imágenes
# ---------------------------------------------------------------------------
@router.get(
    "",
    response_model=ImagenListResponse,
    summary="Listar imágenes del sistema",
)
def listar_imagenes(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Máximo de registros"),
    solo_mias: bool = Query(
        False, description="Si es True, solo muestra imágenes del usuario actual"
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista imágenes con paginación. Admins ven todas; usuarios filtran las propias."""
    usuario_id = current_user.id if solo_mias or current_user.role != "admin" else None
    imagenes, total = get_imagenes(db=db, usuario_id=usuario_id, skip=skip, limit=limit)
    return ImagenListResponse(total=total, imagenes=imagenes)


# ---------------------------------------------------------------------------
# GET /imagenes/{imagen_id} — Detalle de una imagen
# ---------------------------------------------------------------------------
@router.get(
    "/{imagen_id}",
    response_model=ImagenResponse,
    summary="Obtener detalle de una imagen",
)
def detalle_imagen(
    imagen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene los metadatos y resultado IA de una imagen específica."""
    imagen = get_imagen_by_id(db=db, imagen_id=imagen_id)
    if not imagen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada",
        )

    # Usuarios normales solo pueden ver sus propias imágenes
    if current_user.role != "admin" and imagen.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta imagen",
        )

    return imagen


# ---------------------------------------------------------------------------
# DELETE /imagenes/{imagen_id} — Eliminar imagen (solo admin)
# ---------------------------------------------------------------------------
@router.delete(
    "/{imagen_id}",
    response_model=ImagenDeleteResponse,
    dependencies=[Depends(require_role("admin"))],
    summary="Eliminar una imagen (solo admin)",
)
def eliminar_imagen(
    imagen_id: int,
    db: Session = Depends(get_db),
):
    """Elimina una imagen del disco y de la base de datos."""
    deleted = delete_imagen(db=db, imagen_id=imagen_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada",
        )
    return ImagenDeleteResponse(
        detail="Imagen eliminada correctamente",
        imagen_id=imagen_id,
    )


# ---------------------------------------------------------------------------
# POST /imagenes/cleanup — Limpieza de archivos temporales (solo admin)
# ---------------------------------------------------------------------------
@router.post(
    "/cleanup",
    dependencies=[Depends(require_role("admin"))],
    summary="Limpiar archivos huérfanos (solo admin)",
)
def limpiar_archivos_temporales(
    max_age_hours: int = Query(
        24, ge=1, description="Antigüedad mínima en horas para eliminar"
    ),
):
    """
    Elimina archivos en el directorio de uploads que no tienen
    registro en la base de datos y superan la antigüedad indicada.
    """
    removed = cleanup_temp_files(max_age_hours=max_age_hours)
    return {
        "detail": f"Limpieza completada. {removed} archivo(s) eliminado(s).",
        "archivos_eliminados": removed,
    }
