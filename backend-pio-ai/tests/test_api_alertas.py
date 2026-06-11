import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.alertas import Alerta, NotificacionInterna
from app.models.users import User

def test_alertas_crud_endpoints(client: TestClient, user_headers, admin_headers, db_session: Session):
    # 1. Crear Alerta
    response = client.post(
        "/alertas",
        json={"tipo": "temperatura", "titulo": "Fiebre detectada", "descripcion": "Pabellón 5 sobre los 38 grados", "prioridad": "alta"},
        headers=user_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["titulo"] == "Fiebre detectada"
    assert data["estado"] == "activa"
    alerta_id = data["id"]
    
    # 2. Listar Alertas
    response = client.get("/alertas", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == 1
    assert response.json()["alertas"][0]["id"] == alerta_id
    
    # 3. Detalle Alerta
    response = client.get(f"/alertas/{alerta_id}", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == alerta_id
    
    # 4. Marcar como Leída
    response = client.patch(f"/alertas/{alerta_id}/leida", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["estado"] == "leida"
    
    # 5. Atender Alerta
    response = client.patch(
        f"/alertas/{alerta_id}/atender",
        json={"justificacion": "Se activaron ventiladores auxiliares"},
        headers=user_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["estado"] == "atendida"
    assert response.json()["justificacion_cierre"] == "Se activaron ventiladores auxiliares"

def test_alerta_delete_permissions(client: TestClient, user_headers, admin_headers, db_session: Session):
    # Crear alerta
    response = client.post(
        "/alertas",
        json={"tipo": "mortalidad", "titulo": "Grave mortalidad", "descripcion": "Muchos decesos hoy", "prioridad": "critica"},
        headers=admin_headers
    )
    alerta_id = response.json()["id"]
    
    # Intento de eliminación por usuario común -> Forbidden (403)
    response_del_user = client.request(
        "DELETE", 
        f"/alertas/{alerta_id}", 
        json={"justificacion": "Eliminación por usuario común"}, 
        headers=user_headers
    )
    assert response_del_user.status_code == status.HTTP_403_FORBIDDEN
    
    # Intento de eliminación por admin -> OK (200)
    response_del_admin = client.request(
        "DELETE",
        f"/alertas/{alerta_id}",
        json={"justificacion": "Eliminación por el administrador debido a falso positivo de sensores"},
        headers=admin_headers
    )
    assert response_del_admin.status_code == status.HTTP_200_OK
    assert response_del_admin.json()["eliminada"] is True
    
    # Después de eliminada, usuario normal no debe encontrarla
    response_get = client.get(f"/alertas/{alerta_id}", headers=user_headers)
    assert response_get.status_code == status.HTTP_404_NOT_FOUND
    
    # Admin sí puede obtener detalles o listar incluyendo eliminadas
    response_admin_get = client.get(f"/alertas/{alerta_id}", headers=admin_headers)
    assert response_admin_get.status_code == status.HTTP_200_OK
    
    response_list = client.get("/alertas?incluir_eliminadas=true", headers=admin_headers)
    assert response_list.status_code == status.HTTP_200_OK
    assert len(response_list.json()["alertas"]) == 1

def test_alerta_historial_endpoint(client: TestClient, user_headers):
    # Crear alerta
    response = client.post(
        "/alertas",
        json={"tipo": "alimentacion", "titulo": "Sin alimento", "descripcion": "Tolva vacía", "prioridad": "media"},
        headers=user_headers
    )
    alerta_id = response.json()["id"]
    
    # Consultar historial
    response_hist = client.get(f"/alertas/{alerta_id}/historial", headers=user_headers)
    assert response_hist.status_code == status.HTTP_200_OK
    data = response_hist.json()
    assert data["alerta_id"] == alerta_id
    assert data["total"] == 1
    assert data["entradas"][0]["accion"] == "creada"

def test_notificaciones_api_endpoints(client: TestClient, admin_headers, db_session: Session):
    # Crear un admin para que reciba la notificación
    admin = db_session.query(User).filter(User.email == "admin@test.com").first()
    
    # Crear alerta (esto creará la notificación para el admin)
    client.post(
        "/alertas",
        json={"tipo": "temperatura", "titulo": "Fiebre detectada", "descripcion": "Detalle", "prioridad": "alta"},
        headers=admin_headers
    )
    
    # Listar notificaciones del admin
    response = client.get("/notificaciones", headers=admin_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["total"] == 1
    assert data["no_leidas"] == 1
    notif_id = data["notificaciones"][0]["id"]
    
    # Marcar individual como leída
    response_read = client.patch(f"/notificaciones/{notif_id}/leida", headers=admin_headers)
    assert response_read.status_code == status.HTTP_200_OK
    assert response_read.json()["leida"] is True
    
    # Marcar todas leídas
    response_all = client.patch("/notificaciones/marcar-todas-leidas", headers=admin_headers)
    assert response_all.status_code == status.HTTP_200_OK
    assert "actualizadas" in response_all.json()
