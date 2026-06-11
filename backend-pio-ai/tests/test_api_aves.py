import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.aves import Ave, ProduccionHuevos

def test_aves_endpoints_require_auth(client: TestClient):
    # Sin cabecera de autenticación debe dar 401
    response = client.get("/aves")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_aves_crud_endpoints(client: TestClient, user_headers):
    # 1. Registrar Ave
    response = client.post(
        "/aves",
        json={"tipo": "gallina", "cantidad": 150, "raza": "Criolla", "notas": "Lote B"},
        headers=user_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["tipo"] == "gallina"
    assert data["cantidad"] == 150
    ave_id = data["id"]
    
    # 2. Listar Aves
    response = client.get("/aves", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    aves = response.json()
    assert len(aves) == 1
    assert aves[0]["id"] == ave_id
    
    # 3. Editar Ave
    response = client.put(
        f"/aves/{ave_id}",
        json={"cantidad": 160, "notas": "Actualización"},
        headers=user_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["cantidad"] == 160
    assert response.json()["notas"] == "Actualización"
    
    # Editar Ave no existente
    response = client.put(
        "/aves/999",
        json={"cantidad": 160},
        headers=user_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

def test_produccion_endpoints(client: TestClient, user_headers, db_session: Session):
    # Crear un ave directamente en la BD
    ave = Ave(tipo="gallina", cantidad=50)
    db_session.add(ave)
    db_session.commit()
    db_session.refresh(ave)
    
    # 1. Registrar Producción
    response = client.post(
        "/produccion-huevos",
        json={"ave_id": ave.id, "cantidad_huevos": 45, "notas": "Registro mañana"},
        headers=user_headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["ave_id"] == ave.id
    assert data["cantidad_huevos"] == 45
    prod_id = data["id"]
    
    # Registrar producción para ave inexistente
    response = client.post(
        "/produccion-huevos",
        json={"ave_id": 999, "cantidad_huevos": 45},
        headers=user_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    
    # 2. Listar Producciones
    response = client.get("/produccion-huevos", headers=user_headers)
    assert response.status_code == status.HTTP_200_OK
    prods = response.json()
    assert len(prods) == 1
    assert prods[0]["id"] == prod_id
    
    # 3. Editar Producción
    response = client.put(
        f"/produccion-huevos/{prod_id}",
        json={"cantidad_huevos": 48, "notas": "Corregido"},
        headers=user_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["cantidad_huevos"] == 48
    
    # Editar producción no existente
    response = client.put(
        "/produccion-huevos/999",
        json={"cantidad_huevos": 5},
        headers=user_headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
