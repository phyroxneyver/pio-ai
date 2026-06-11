import pytest
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.users import User
from app.models.alertas import Alerta, HistorialAlerta, NotificacionInterna
from app.schemas.alertas import AlertaCreate
from app.services.alertas import (
    crear_alerta,
    listar_alertas,
    obtener_alerta,
    marcar_como_leida,
    atender_alerta,
    eliminar_alerta,
    listar_notificaciones,
    marcar_notificacion_leida,
    marcar_todas_leidas,
    obtener_historial
)

@pytest.fixture
def test_users_for_alert(db_session: Session):
    """Crea un administrador y un usuario común para pruebas de alertas."""
    admin = User(email="adm_alert@test.com", hashed_password="pw", role="admin", is_active=True)
    user = User(email="usr_alert@test.com", hashed_password="pw", role="usuario", is_active=True)
    db_session.add_all([admin, user])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(user)
    return admin, user

def test_crear_alerta_notifica_admins(db_session: Session, test_users_for_alert):
    admin, user = test_users_for_alert
    
    alerta_in = AlertaCreate(tipo="mortalidad", titulo="Aves muertas", descripcion="Descripción de prueba más larga", prioridad="alta")
    
    alerta = crear_alerta(db=db_session, datos=alerta_in, creado_por_id=user.id)
    
    assert alerta.id is not None
    assert alerta.estado == "activa"
    assert alerta.creado_por_id == user.id
    
    # Validar historial creado
    hist = db_session.query(HistorialAlerta).filter(HistorialAlerta.alerta_id == alerta.id).all()
    assert len(hist) == 1
    assert hist[0].accion == "creada"
    assert hist[0].estado_nuevo == "activa"
    assert hist[0].realizado_por_id == user.id
    
    # Validar que se notificó al admin activo
    notifs = db_session.query(NotificacionInterna).filter(NotificacionInterna.alerta_id == alerta.id).all()
    assert len(notifs) == 1
    assert notifs[0].usuario_id == admin.id
    assert notifs[0].leida is False

def test_marcar_como_leida_service(db_session: Session, test_users_for_alert):
    admin, user = test_users_for_alert
    alerta_in = AlertaCreate(tipo="temperatura", titulo="Temp alta", descripcion="Pabellón 2", prioridad="media")
    alerta = crear_alerta(db=db_session, datos=alerta_in, creado_por_id=user.id)
    
    # Transición válida: activa -> leida
    alerta_leida = marcar_como_leida(db=db_session, alerta_id=alerta.id, usuario_id=user.id)
    assert alerta_leida.estado == "leida"
    
    # Intentar marcar leída de nuevo (error porque ya no está "activa")
    with pytest.raises(HTTPException) as exc_info:
        marcar_como_leida(db=db_session, alerta_id=alerta.id, usuario_id=user.id)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

def test_atender_alerta_service(db_session: Session, test_users_for_alert):
    admin, user = test_users_for_alert
    alerta_in = AlertaCreate(tipo="alimentacion", titulo="Poca comida", descripcion="Tolva vacía", prioridad="baja")
    alerta = crear_alerta(db=db_session, datos=alerta_in, creado_por_id=user.id)
    
    justificacion = "Se procedió a rellenar la tolva manualmente."
    
    # Transición válida: activa -> atendida
    alerta_atendida = atender_alerta(
        db=db_session,
        alerta_id=alerta.id,
        usuario_id=user.id,
        justificacion=justificacion
    )
    
    assert alerta_atendida.estado == "atendida"
    assert alerta_atendida.atendido_por_id == user.id
    assert alerta_atendida.justificacion_cierre == justificacion
    
    # Intentar atender de nuevo (ya está atendida)
    with pytest.raises(HTTPException) as exc_info:
        atender_alerta(db=db_session, alerta_id=alerta.id, usuario_id=user.id, justificacion="otra")
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

def test_eliminar_alerta_soft_delete(db_session: Session, test_users_for_alert):
    admin, user = test_users_for_alert
    alerta_in = AlertaCreate(tipo="otro", titulo="Falso positivo", descripcion="Ruido de sensores", prioridad="baja")
    alerta = crear_alerta(db=db_session, datos=alerta_in, creado_por_id=user.id)
    
    justificacion = "Fue una alerta duplicada por error técnico."
    alerta_eliminada = eliminar_alerta(
        db=db_session,
        alerta_id=alerta.id,
        usuario_id=admin.id,
        justificacion=justificacion
    )
    
    assert alerta_eliminada.eliminada is True
    assert alerta_eliminada.justificacion_eliminacion == justificacion
    assert alerta_eliminada.eliminada_por_id == admin.id
    
    # Intentar eliminar de nuevo
    with pytest.raises(HTTPException) as exc_info:
        eliminar_alerta(db=db_session, alerta_id=alerta.id, usuario_id=admin.id, justificacion="otra")
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST

def test_notificaciones_listar_y_marcar(db_session: Session, test_users_for_alert):
    admin, user = test_users_for_alert
    alerta_in = AlertaCreate(tipo="temperatura", titulo="Temp baja", descripcion="Pabellón 1", prioridad="critica")
    alerta = crear_alerta(db=db_session, datos=alerta_in, creado_por_id=user.id)
    
    # Listar notificaciones del admin (debe tener 1 no leída)
    notifs, total, no_leidas = listar_notificaciones(db=db_session, usuario_id=admin.id)
    assert total == 1
    assert no_leidas == 1
    assert notifs[0].leida is False
    
    # Marcar leída
    notif_id = notifs[0].id
    marcar_notificacion_leida(db=db_session, notificacion_id=notif_id, usuario_id=admin.id)
    
    # Verificar cambios
    _, _, no_leidas_despues = listar_notificaciones(db=db_session, usuario_id=admin.id)
    assert no_leidas_despues == 0
    
    # Marcar todas leídas (por si hay más)
    count = marcar_todas_leidas(db=db_session, usuario_id=admin.id)
    assert count == 0  # Ya estaba leída

def test_obtener_historial(db_session: Session, test_users_for_alert):
    admin, user = test_users_for_alert
    alerta_in = AlertaCreate(tipo="mortalidad", titulo="Aves muertas", descripcion="Cinco", prioridad="alta")
    alerta = crear_alerta(db=db_session, datos=alerta_in, creado_por_id=user.id)
    
    marcar_como_leida(db=db_session, alerta_id=alerta.id, usuario_id=user.id)
    atender_alerta(db=db_session, alerta_id=alerta.id, usuario_id=admin.id, justificacion="Se atendió rápido")
    
    historial = obtener_historial(db=db_session, alerta_id=alerta.id)
    # 3 acciones: creada, leida, atendida
    assert len(historial) == 3
    acciones = [h.accion for h in historial]
    # Se listan desc (más reciente primero)
    assert acciones == ["atendida", "leida", "creada"]
