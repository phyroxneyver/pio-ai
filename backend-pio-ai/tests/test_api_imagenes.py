import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
import json

from app.models.imagenes import Imagen, ResultadoIA, FeedbackIA
from app.models.users import User

@pytest.fixture
def mock_upload_services():
    """Mockea servicios de Cloudinary y verificación de calidad para subida limpia."""
    with patch("app.services.imagenes._verificar_calidad") as mock_qual, \
         patch("app.services.imagenes.cloudinary.uploader.upload") as mock_cloud, \
         patch("app.services.ia_service.analizar_imagen_con_ia") as mock_ia:  # Ruta corregida aquí
        
        mock_qual.return_value = None
        mock_cloud.return_value = {"secure_url": "https://res.cloudinary.com/test.jpg"}
        mock_ia.return_value = MagicMock(
            spec=ResultadoIA, 
            id=10, 
            imagen_id=1, 
            conteo_pollitos=5, 
            confianza="alta", 
            estado="completado",
            precision_estimada=0.92,
            notas_ia='{"conteo_gallinas": 2, "conteo_huevos": 4, "notas": "OK"}',
            detecciones=[]
        )
        yield mock_qual, mock_cloud, mock_ia

@patch("app.api.imagenes.analizar_imagen_con_ia")
def test_api_upload_imagen(mock_ia, client: TestClient, user_headers, mock_upload_services):
    file_payload = {"file": ("test.jpg", b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;', "image/jpeg")}
    response = client.post("/imagenes/upload", files=file_payload, headers=user_headers)
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["nombre_original"] == "test.jpg"
    assert data["ruta"] == "https://res.cloudinary.com/test.jpg"
    assert "id" in data

def test_api_list_and_detail_imagen(client: TestClient, user_headers, admin_headers, db_session: Session):
    img1 = Imagen(nombre_original="test1.jpg", nombre_almacenado="store1.jpg", ruta="http://test1.jpg", content_type="image/jpeg", tamaño_bytes=10, hash_archivo="h1", usuario_id=1)
    img2 = Imagen(nombre_original="test2.jpg", nombre_almacenado="store2.jpg", ruta="http://test2.jpg", content_type="image/jpeg", tamaño_bytes=10, hash_archivo="h2", usuario_id=2)
    db_session.add_all([img1, img2])
    db_session.commit()
    
    admin = db_session.query(User).filter(User.email == "admin@test.com").first()
    user = db_session.query(User).filter(User.email == "user@test.com").first()
    
    img1.usuario_id = admin.id
    img2.usuario_id = user.id
    db_session.commit()
    
    response = client.get("/imagenes", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["total"] == 1
    assert response.json()["imagenes"][0]["nombre_original"] == "test2.jpg"
    
    response_admin = client.get("/imagenes", headers=admin_headers)
    assert response_admin.status_code == status.HTTP_200_OK
    assert response_admin.json()["total"] == 2
    
    response_detail = client.get(f"/imagenes/{img2.id}", headers=user_headers)
    assert response_detail.status_code == status.HTTP_200_OK
    assert response_detail.json()["id"] == img2.id
    
    response_forbidden = client.get(f"/imagenes/{img1.id}", headers=user_headers)
    assert response_forbidden.status_code == status.HTTP_403_FORBIDDEN

@patch("app.services.imagenes.cloudinary.uploader.destroy")
def test_api_delete_imagen(mock_destroy, client: TestClient, user_headers, admin_headers, db_session: Session):
    mock_destroy.return_value = {"result": "ok"}
    admin = db_session.query(User).filter(User.email == "admin@test.com").first()
    
    img = Imagen(nombre_original="t.jpg", nombre_almacenado="s.jpg", ruta="http://res.cloudinary.com/pio-ai/upload/v1/t.jpg", content_type="image/jpeg", tamaño_bytes=10, hash_archivo="h_del", usuario_id=admin.id)
    db_session.add(img)
    db_session.commit()
    
    response_user = client.delete(f"/imagenes/{img.id}", headers=user_headers)
    assert response_user.status_code == status.HTTP_403_FORBIDDEN
    
    response_admin = client.delete(f"/imagenes/{img.id}", headers=admin_headers)
    assert response_admin.status_code == status.HTTP_200_OK
    assert response_admin.json()["imagen_id"] == img.id

def test_api_enviar_feedback(client: TestClient, user_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "user@test.com").first()
    
    img = Imagen(nombre_original="fb.jpg", nombre_almacenado="fbs.jpg", ruta="http://fb.jpg", content_type="image/jpeg", tamaño_bytes=10, hash_archivo="h_fb", usuario_id=user.id)
    db_session.add(img)
    db_session.flush()
    
    res = ResultadoIA(imagen_id=img.id, conteo_pollitos=4, estado="completado")
    db_session.add(res)
    db_session.commit()
    
    response = client.post(
        f"/imagenes/{img.id}/feedback",
        json={"conteo_corregido": 6, "tipo_feedback": "correccion", "motivo": "Había dos pollitos ocultos tras la gallina"},
        headers=user_headers
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["conteo_corregido"] == 6
    assert data["conteo_ia"] == 4
    assert data["diferencia"] == 2
    assert data["motivo"] == "Había dos pollitos ocultos tras la gallina"


@patch("app.api.imagenes.analizar_imagen_con_ia")
def test_api_analizar_imagen_manualmente(mock_ia, client: TestClient, user_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "user@test.com").first()
    img = Imagen(nombre_original="manual.jpg", nombre_almacenado="man.jpg", ruta="http://man.jpg", content_type="image/jpeg", tamaño_bytes=10, hash_archivo="h_man", usuario_id=user.id)
    db_session.add(img)
    db_session.commit()
    
    mock_res = MagicMock(
        spec=ResultadoIA,
        id=99,
        imagen_id=img.id,
        conteo_pollitos=12,
        confianza="alta",
        estado="completado",
        error_detalle=None,
        precision_estimada=0.96,
        notas_ia='{"conteo_gallinas": 3, "conteo_huevos": 6, "notas": "Excelente conteo"}',
        detecciones_json='[]'
    )
    mock_ia.return_value = mock_res
    
    response = client.post(f"/imagenes/{img.id}/analizar", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["conteo_pollitos"] == 12
    assert data["conteo_gallinas"] == 3
    assert data["conteo_huevos"] == 6
    assert data["notas_ia"] == "Excelente conteo"

def test_api_obtener_ultima_metrica_ia(client: TestClient, user_headers, db_session: Session):
    user = db_session.query(User).filter(User.email == "user@test.com").first()
    
    response_404 = client.get("/imagenes/ia/metricas/ultima", headers=user_headers)
    assert response_404.status_code == status.HTTP_404_NOT_FOUND
    
    img = Imagen(nombre_original="m.jpg", nombre_almacenado="ms.jpg", ruta="http://cloudinary/m.jpg", content_type="image/jpeg", tamaño_bytes=10, hash_archivo="h_m", usuario_id=user.id)
    db_session.add(img)
    db_session.flush()
    
    from datetime import datetime, timezone
    res = ResultadoIA(
        imagen_id=img.id,
        conteo_pollitos=8,
        confianza="alta",
        estado="completado",
        duracion_ms=1200,
        precision_estimada=0.95,
        procesado_at=datetime.now(timezone.utc)
    )
    db_session.add(res)
    db_session.commit()
    
    response = client.get("/imagenes/ia/metricas/ultima", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["conteo_pollitos"] == 8
    assert data["duracion_ms"] == 1200
    assert data["precision_estimada"] == 0.95
    assert data["imagen_url"] == "http://cloudinary/m.jpg"