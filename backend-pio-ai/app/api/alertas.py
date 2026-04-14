"""
Router de alertas y notificaciones — Sistema de monitoreo avícola.

Endpoints:
  POST   /alertas                              → Crear alerta
  GET    /alertas                              → Listar alertas (filtros)
  GET    /alertas/{id}                         → Detalle de alerta
  PATCH  /alertas/{id}/leida                   → Marcar como leída
  PATCH  /alertas/{id}/atender                 → Atender alerta (justificación)
  DELETE /alertas/{id}                         → Eliminar alerta (admin + justificación)
  GET    /alertas/{id}/historial               → Historial completo

  GET    /notificaciones                       → Listar notificaciones del usuario
  PATCH  /notificaciones/{id}/leida            → Marcar notificación leída
  PATCH  /notificaciones/marcar-todas-leidas   → Marcar todas leídas
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_active_user, require_role
from app.models.users import User
from app.schemas.alertas import (
    AlertaAtender,
    AlertaCreate,
    AlertaEliminar,
    AlertaListResponse,
    AlertaResponse,
    HistorialResponse,
    NotificacionListResponse,
    NotificacionResponse,
)
from app.services.alertas import (
    atender_alerta,
    crear_alerta,
    eliminar_alerta,
    listar_alertas,
    listar_notificaciones,
    marcar_como_leida,
    marcar_notificacion_leida,
    marcar_todas_leidas,
    obtener_alerta,
    obtener_historial,
)

router = APIRouter(tags=["Alertas y Notificaciones"])


# ===========================================================================
# ALERTAS
# ===========================================================================

# ---------------------------------------------------------------------------
# POST /alertas — Crear alerta
# ---------------------------------------------------------------------------
@router.post(
    "/alertas",
    response_model=AlertaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva alerta",
)
def crear_nueva_alerta(
    datos: AlertaCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Crea una alerta en el sistema.

    - Genera notificaciones automáticas para todos los admins
    - Registra la acción en el historial de trazabilidad
    """
    return crear_alerta(db=db, datos=datos, creado_por_id=current_user.id)


# ---------------------------------------------------------------------------
# GET /alertas — Listar alertas
# ---------------------------------------------------------------------------
@router.get(
    "/alertas",
    response_model=AlertaListResponse,
    summary="Listar alertas del sistema",
)
def listar_todas_alertas(
    estado: str | None = Query(
        None, description="Filtrar por estado: activa, leida, atendida",
    ),
    prioridad: str | None = Query(
        None, description="Filtrar por prioridad: baja, media, alta, critica",
    ),
    tipo: str | None = Query(
        None, description="Filtrar por tipo: mortalidad, temperatura, etc.",
    ),
    incluir_eliminadas: bool = Query(
        False, description="Incluir alertas eliminadas (solo admin)",
    ),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Máximo de registros"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista alertas con filtros opcionales y paginación."""
    # Solo admin puede ver eliminadas
    if incluir_eliminadas and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden ver alertas eliminadas",
        )

    alertas, total = listar_alertas(
        db=db,
        estado=estado,
        prioridad=prioridad,
        tipo=tipo,
        incluir_eliminadas=incluir_eliminadas,
        skip=skip,
        limit=limit,
    )
    return AlertaListResponse(total=total, alertas=alertas)


# ---------------------------------------------------------------------------
# GET /alertas/{id} — Detalle
# ---------------------------------------------------------------------------
@router.get(
    "/alertas/{alerta_id}",
    response_model=AlertaResponse,
    summary="Obtener detalle de una alerta",
)
def detalle_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene los detalles completos de una alerta."""
    alerta = obtener_alerta(db=db, alerta_id=alerta_id)
    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada",
        )

    # Usuarios normales no ven alertas eliminadas
    if alerta.eliminada and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada",
        )

    return alerta


# ---------------------------------------------------------------------------
# PATCH /alertas/{id}/leida — Marcar como leída
# ---------------------------------------------------------------------------
@router.patch(
    "/alertas/{alerta_id}/leida",
    response_model=AlertaResponse,
    summary="Marcar alerta como leída",
)
def marcar_alerta_leida(
    alerta_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Marca una alerta como leída.

    Transición válida: activa → leída
    """
    return marcar_como_leida(
        db=db, alerta_id=alerta_id, usuario_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# PATCH /alertas/{id}/atender — Atender alerta
# ---------------------------------------------------------------------------
@router.patch(
    "/alertas/{alerta_id}/atender",
    response_model=AlertaResponse,
    summary="Atender una alerta (requiere justificación)",
)
def atender_una_alerta(
    alerta_id: int,
    datos: AlertaAtender,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Marca una alerta como atendida con justificación obligatoria.

    Transición válida: activa|leída → atendida
    """
    return atender_alerta(
        db=db,
        alerta_id=alerta_id,
        usuario_id=current_user.id,
        justificacion=datos.justificacion,
    )


# ---------------------------------------------------------------------------
# DELETE /alertas/{id} — Eliminar alerta (solo admin + justificación)
# ---------------------------------------------------------------------------
@router.delete(
    "/alertas/{alerta_id}",
    response_model=AlertaResponse,
    summary="Eliminar alerta (solo admin, requiere justificación)",
)
def eliminar_una_alerta(
    alerta_id: int,
    datos: AlertaEliminar,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    """
    Soft-delete de una alerta.

    - Solo administradores pueden ejecutar esta acción
    - Requiere justificación obligatoria (mín. 10 caracteres)
    - La alerta no se borra de la BD, se marca como eliminada
    - Se registra en el historial para auditoría
    """
    return eliminar_alerta(
        db=db,
        alerta_id=alerta_id,
        usuario_id=current_user.id,
        justificacion=datos.justificacion,
    )


# ---------------------------------------------------------------------------
# GET /alertas/{id}/historial — Historial completo
# ---------------------------------------------------------------------------
@router.get(
    "/alertas/{alerta_id}/historial",
    response_model=HistorialResponse,
    summary="Historial completo de una alerta",
    dependencies=[Depends(get_current_active_user)],
)
def historial_alerta(
    alerta_id: int,
    db: Session = Depends(get_db),
):
    """
    Obtiene el historial completo de cambios de una alerta.

    Muestra: quién hizo qué, cuándo, y con qué justificación.
    Garantiza trazabilidad total.
    """
    entradas = obtener_historial(db=db, alerta_id=alerta_id)
    return HistorialResponse(
        alerta_id=alerta_id,
        total=len(entradas),
        entradas=entradas,
    )


# ===========================================================================
# NOTIFICACIONES
# ===========================================================================

# ---------------------------------------------------------------------------
# GET /notificaciones — Listar notificaciones del usuario
# ---------------------------------------------------------------------------
@router.get(
    "/notificaciones",
    response_model=NotificacionListResponse,
    summary="Listar notificaciones del usuario actual",
)
def listar_mis_notificaciones(
    solo_no_leidas: bool = Query(
        False, description="Mostrar solo notificaciones no leídas",
    ),
    skip: int = Query(0, ge=0, description="Registros a saltar"),
    limit: int = Query(50, ge=1, le=100, description="Máximo de registros"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Lista las notificaciones del usuario autenticado con conteo de no leídas."""
    notificaciones, total, no_leidas = listar_notificaciones(
        db=db,
        usuario_id=current_user.id,
        solo_no_leidas=solo_no_leidas,
        skip=skip,
        limit=limit,
    )
    return NotificacionListResponse(
        total=total,
        no_leidas=no_leidas,
        notificaciones=notificaciones,
    )


# ---------------------------------------------------------------------------
# PATCH /notificaciones/{id}/leida — Marcar notificación leída
# ---------------------------------------------------------------------------
@router.patch(
    "/notificaciones/{notificacion_id}/leida",
    response_model=NotificacionResponse,
    summary="Marcar notificación como leída",
)
def marcar_notif_leida(
    notificacion_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Marca una notificación individual como leída."""
    return marcar_notificacion_leida(
        db=db,
        notificacion_id=notificacion_id,
        usuario_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# PATCH /notificaciones/marcar-todas-leidas
# ---------------------------------------------------------------------------
@router.patch(
    "/notificaciones/marcar-todas-leidas",
    summary="Marcar todas las notificaciones como leídas",
)
def marcar_todas_notif_leidas(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Marca todas las notificaciones no leídas del usuario como leídas."""
    count = marcar_todas_leidas(db=db, usuario_id=current_user.id)
    return {
        "detail": f"{count} notificación(es) marcada(s) como leída(s).",
        "actualizadas": count,
    }
