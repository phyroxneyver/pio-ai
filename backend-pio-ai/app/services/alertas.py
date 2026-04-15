from typing import Optional, List
"""
Servicio de alertas, notificaciones e historial.

Responsabilidades:
- CRUD de alertas con validación de estados
- Transiciones: activa → leída → atendida (con justificación)
- Soft-delete con justificación obligatoria (solo admin)
- Notificaciones internas por usuario
- Registro inmutable de cada acción (historial/trazabilidad)
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models.alertas import Alerta, HistorialAlerta, NotificacionInterna
from ..models.users import User
from ..schemas.alertas import AlertaCreate


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------
def _registrar_historial(
    db: Session,
    alerta_id: int,
    accion: str,
    realizado_por_id: int,
    estado_anterior: Optional[str] = None,
    estado_nuevo: Optional[str] = None,
    detalle: Optional[str] = None,
) -> HistorialAlerta:
    """Registra una entrada inmutable en el historial de la alerta."""
    entrada = HistorialAlerta(
        alerta_id=alerta_id,
        accion=accion,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        detalle=detalle,
        realizado_por_id=realizado_por_id,
    )
    db.add(entrada)
    return entrada


def _notificar_admins(db: Session, alerta_id: int) -> None:
    """Crea notificaciones internas para todos los admins activos."""
    admins = (
        db.query(User)
        .filter(User.role == "admin", User.is_active == True)
        .all()
    )
    for admin in admins:
        notif = NotificacionInterna(
            alerta_id=alerta_id,
            usuario_id=admin.id,
        )
        db.add(notif)


# ---------------------------------------------------------------------------
# CRUD de Alertas
# ---------------------------------------------------------------------------
def crear_alerta(
    db: Session, datos: AlertaCreate, creado_por_id: int,
) -> Alerta:
    """
    Crea una nueva alerta y genera:
    - Registro en historial (acción: 'creada')
    - Notificaciones para todos los admins activos
    """
    alerta = Alerta(
        tipo=datos.tipo,
        titulo=datos.titulo,
        descripcion=datos.descripcion,
        prioridad=datos.prioridad,
        estado="activa",
        creado_por_id=creado_por_id,
    )
    db.add(alerta)
    db.flush()  # Obtener ID

    # Historial
    _registrar_historial(
        db=db,
        alerta_id=alerta.id,
        accion="creada",
        estado_nuevo="activa",
        detalle=f"Alerta creada: {datos.titulo}",
        realizado_por_id=creado_por_id,
    )

    # Notificar admins
    _notificar_admins(db, alerta.id)

    db.commit()
    db.refresh(alerta)
    return alerta


def listar_alertas(
    db: Session,
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    tipo: Optional[str] = None,
    incluir_eliminadas: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[Alerta], int]:
    """
    Lista alertas con filtros opcionales y paginación.
    Por defecto oculta las eliminadas (soft-delete).
    """
    query = db.query(Alerta)

    if not incluir_eliminadas:
        query = query.filter(Alerta.eliminada == False)
    if estado:
        query = query.filter(Alerta.estado == estado)
    if prioridad:
        query = query.filter(Alerta.prioridad == prioridad)
    if tipo:
        query = query.filter(Alerta.tipo == tipo)

    total = query.count()
    alertas = (
        query.order_by(Alerta.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return alertas, total


def obtener_alerta(db: Session, alerta_id: int) -> Optional[Alerta]:
    """Obtiene una alerta por ID (incluye eliminadas para auditoría)."""
    return db.query(Alerta).filter(Alerta.id == alerta_id).first()


def marcar_como_leida(
    db: Session, alerta_id: int, usuario_id: int,
) -> Alerta:
    """
    Marca una alerta como leída.
    Transición válida: activa → leida
    """
    alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()
    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada",
        )

    if alerta.eliminada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar una alerta eliminada",
        )

    if alerta.estado not in ("activa",):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede marcar como leída una alerta en estado '{alerta.estado}'. "
                   f"Solo alertas activas pueden marcarse como leídas.",
        )

    estado_anterior = alerta.estado
    alerta.estado = "leida"

    _registrar_historial(
        db=db,
        alerta_id=alerta.id,
        accion="leida",
        estado_anterior=estado_anterior,
        estado_nuevo="leida",
        detalle="Alerta marcada como leída",
        realizado_por_id=usuario_id,
    )

    db.commit()
    db.refresh(alerta)
    return alerta


def atender_alerta(
    db: Session, alerta_id: int, usuario_id: int, justificacion: str,
) -> Alerta:
    """
    Marca una alerta como atendida con justificación obligatoria.
    Transición válida: activa|leida → atendida
    """
    alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()
    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada",
        )

    if alerta.eliminada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede atender una alerta eliminada",
        )

    if alerta.estado not in ("activa", "leida"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede atender una alerta en estado '{alerta.estado}'. "
                   f"Solo alertas activas o leídas pueden atenderse.",
        )

    estado_anterior = alerta.estado
    alerta.estado = "atendida"
    alerta.atendido_por_id = usuario_id
    alerta.justificacion_cierre = justificacion

    _registrar_historial(
        db=db,
        alerta_id=alerta.id,
        accion="atendida",
        estado_anterior=estado_anterior,
        estado_nuevo="atendida",
        detalle=f"Justificación: {justificacion}",
        realizado_por_id=usuario_id,
    )

    db.commit()
    db.refresh(alerta)
    return alerta


def eliminar_alerta(
    db: Session, alerta_id: int, usuario_id: int, justificacion: str,
) -> Alerta:
    """
    Soft-delete de una alerta con justificación obligatoria.
    Solo admin puede ejecutar esta acción.
    No se elimina de la BD para mantener trazabilidad.
    """
    alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()
    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada",
        )

    if alerta.eliminada:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta alerta ya fue eliminada",
        )

    estado_anterior = alerta.estado
    alerta.eliminada = True
    alerta.justificacion_eliminacion = justificacion
    alerta.eliminada_por_id = usuario_id
    alerta.eliminada_at = datetime.now(timezone.utc)

    _registrar_historial(
        db=db,
        alerta_id=alerta.id,
        accion="eliminada",
        estado_anterior=estado_anterior,
        estado_nuevo=alerta.estado,
        detalle=f"Justificación: {justificacion}",
        realizado_por_id=usuario_id,
    )

    db.commit()
    db.refresh(alerta)
    return alerta


# ---------------------------------------------------------------------------
# Notificaciones internas
# ---------------------------------------------------------------------------
def listar_notificaciones(
    db: Session,
    usuario_id: int,
    solo_no_leidas: bool = False,
    skip: int = 0,
    limit: int = 50,
) -> tuple[List[NotificacionInterna], int, int]:
    """
    Lista notificaciones de un usuario con paginación.
    Retorna: (notificaciones, total, no_leidas)
    """
    query = db.query(NotificacionInterna).filter(
        NotificacionInterna.usuario_id == usuario_id,
    )

    if solo_no_leidas:
        query = query.filter(NotificacionInterna.leida == False)

    total = query.count()

    # Contar no leídas (siempre, independiente del filtro)
    no_leidas = (
        db.query(NotificacionInterna)
        .filter(
            NotificacionInterna.usuario_id == usuario_id,
            NotificacionInterna.leida == False,
        )
        .count()
    )

    notificaciones = (
        query.order_by(NotificacionInterna.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return notificaciones, total, no_leidas


def marcar_notificacion_leida(
    db: Session, notificacion_id: int, usuario_id: int,
) -> NotificacionInterna:
    """Marca una notificación como leída."""
    notif = (
        db.query(NotificacionInterna)
        .filter(
            NotificacionInterna.id == notificacion_id,
            NotificacionInterna.usuario_id == usuario_id,
        )
        .first()
    )
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notificación no encontrada",
        )

    if notif.leida:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta notificación ya fue marcada como leída",
        )

    notif.leida = True
    notif.leida_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(notif)
    return notif


def marcar_todas_leidas(db: Session, usuario_id: int) -> int:
    """Marca todas las notificaciones no leídas del usuario como leídas."""
    ahora = datetime.now(timezone.utc)
    count = (
        db.query(NotificacionInterna)
        .filter(
            NotificacionInterna.usuario_id == usuario_id,
            NotificacionInterna.leida == False,
        )
        .update({"leida": True, "leida_at": ahora})
    )
    db.commit()
    return count


# ---------------------------------------------------------------------------
# Historial (trazabilidad)
# ---------------------------------------------------------------------------
def obtener_historial(
    db: Session, alerta_id: int,
) -> List[HistorialAlerta]:
    """Obtiene el historial completo de una alerta (orden cronológico desc)."""
    # Verificar que la alerta existe
    alerta = db.query(Alerta).filter(Alerta.id == alerta_id).first()
    if not alerta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alerta no encontrada",
        )

    return (
        db.query(HistorialAlerta)
        .filter(HistorialAlerta.alerta_id == alerta_id)
        .order_by(HistorialAlerta.created_at.desc())
        .all()
    )
