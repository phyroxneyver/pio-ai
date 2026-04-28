"""
Router de imágenes — Endpoints protegidos para gestión de imágenes avícolas.
"""
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.deps import get_current_active_user, require_role
from ..models.imagenes import FeedbackIA, Imagen, ResultadoIA
from ..models.users import User
from ..schemas.imagenes import (
    FeedbackIACreate,
    FeedbackIAResponse,
    ImagenDeleteResponse,
    ImagenListResponse,
    ImagenResponse,
    UltimaMetricaIAResponse,
)
from ..services.imagenes import (
    cleanup_temp_files,
    delete_imagen,
    get_imagen_by_id,
    get_imagenes,
    upload_imagen,
)

router = APIRouter(prefix="/imagenes", tags=["Imágenes"])


@router.post(
    "/upload",
    response_model=ImagenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subir una imagen para análisis",
)
async def subir_imagen(
    file: UploadFile = File(..., description="Archivo de imagen JPG o PNG, máx. 10 MB"),
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


@router.get(
    "",
    response_model=ImagenListResponse,
    summary="Listar imágenes del sistema",
)
def listar_imagenes(
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Máximo de registros"),
    solo_mias: bool = Query(False, description="Si es True, solo muestra imágenes del usuario actual"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    usuario_id = current_user.id if solo_mias or current_user.role != "admin" else None

    imagenes, total = get_imagenes(
        db=db,
        usuario_id=usuario_id,
        skip=skip,
        limit=limit,
    )

    return ImagenListResponse(
        total=total,
        imagenes=imagenes,
    )


@router.get(
    "/ia/metricas/ultima",
    response_model=UltimaMetricaIAResponse,
    summary="Última métrica técnica de IA",
)
def obtener_ultima_metrica_ia(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = (
        db.query(ResultadoIA)
        .join(Imagen, Imagen.id == ResultadoIA.imagen_id)
        .filter(ResultadoIA.procesado_at.isnot(None))
    )

    if current_user.role != "admin":
        query = query.filter(Imagen.usuario_id == current_user.id)

    resultado = query.order_by(ResultadoIA.procesado_at.desc()).first()

    if not resultado or not resultado.imagen:
        raise HTTPException(
            status_code=404,
            detail="Todavía no hay métricas de IA",
        )

    return UltimaMetricaIAResponse(
        imagen_id=resultado.imagen_id,
        resultado_id=resultado.id,
        conteo_pollitos=resultado.conteo_pollitos,
        confianza=resultado.confianza,
        estado=resultado.estado,
        duracion_ms=resultado.duracion_ms,
        precision_estimada=resultado.precision_estimada,
        notas_ia=resultado.notas_ia,
        procesado_at=resultado.procesado_at,
        imagen_url=resultado.imagen.ruta,
    )


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
    imagen = get_imagen_by_id(db=db, imagen_id=imagen_id)

    if not imagen:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada",
        )

    if current_user.role != "admin" and imagen.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para ver esta imagen",
        )

    return imagen


@router.delete(
    "/{imagen_id}",
    response_model=ImagenDeleteResponse,
    dependencies=[Depends(require_role("admin"))],
    summary="Eliminar una imagen solo admin",
)
def eliminar_imagen(
    imagen_id: int,
    db: Session = Depends(get_db),
):
    deleted = delete_imagen(
        db=db,
        imagen_id=imagen_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Imagen no encontrada",
        )

    return ImagenDeleteResponse(
        detail="Imagen eliminada correctamente",
        imagen_id=imagen_id,
    )


@router.post(
    "/cleanup",
    dependencies=[Depends(require_role("admin"))],
    summary="Limpiar archivos huérfanos solo admin",
)
def limpiar_archivos_temporales(
    max_age_hours: int = Query(24, ge=1),
):
    removed = cleanup_temp_files(max_age_hours=max_age_hours)

    return {
        "detail": f"Limpieza completada. {removed} archivo(s) eliminado(s).",
        "archivos_eliminados": removed,
    }


@router.post(
    "/{imagen_id}/analizar",
    response_model=dict,
    summary="Analizar imagen con IA",
)
def analizar_imagen(
    imagen_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    imagen = get_imagen_by_id(
        db=db,
        imagen_id=imagen_id,
    )

    if not imagen:
        raise HTTPException(
            status_code=404,
            detail="Imagen no encontrada",
        )

    if current_user.role != "admin" and imagen.usuario_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para analizar esta imagen",
        )

    from ..services.ia_service import analizar_imagen_con_ia

    resultado = analizar_imagen_con_ia(
        db=db,
        imagen_id=imagen_id,
    )

    return {
        "id": resultado.id,
        "imagen_id": resultado.imagen_id,
        "conteo_pollitos": resultado.conteo_pollitos,
        "confianza": resultado.confianza,
        "estado": resultado.estado,
        "error_detalle": resultado.error_detalle,
        "procesado_at": resultado.procesado_at,
        "created_at": resultado.created_at,
        "duracion_ms": resultado.duracion_ms,
        "precision_estimada": resultado.precision_estimada,
        "notas_ia": resultado.notas_ia,
        "detecciones": resultado.detecciones,
    }


@router.post(
    "/{imagen_id}/feedback",
    response_model=FeedbackIAResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Guardar corrección o foto fallida para entrenamiento futuro",
)
def enviar_feedback_ia(
    imagen_id: int,
    datos: FeedbackIACreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    imagen = get_imagen_by_id(
        db=db,
        imagen_id=imagen_id,
    )

    if not imagen:
        raise HTTPException(
            status_code=404,
            detail="Imagen no encontrada",
        )

    if current_user.role != "admin" and imagen.usuario_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para enviar feedback de esta imagen",
        )

    resultado = imagen.resultado_ia
    conteo_ia = resultado.conteo_pollitos if resultado else None
    diferencia = datos.conteo_corregido - (conteo_ia or 0)

    feedback = FeedbackIA(
        imagen_id=imagen.id,
        resultado_ia_id=resultado.id if resultado else None,
        usuario_id=current_user.id,
        conteo_ia=conteo_ia,
        conteo_corregido=datos.conteo_corregido,
        diferencia=diferencia,
        tipo_feedback=datos.tipo_feedback,
        motivo=datos.motivo,
        imagen_url=imagen.ruta,
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback