import pytest
from fastapi import status
from fastapi.testclient import TestClient
from app.core.ml import ml_models
from app.api.predict import calcular_precision, procesar_imagen_sincrono
import cv2
import numpy as np

def test_calcular_precision():
    # Caso 1: Conteo manual es 0, IA es 0 -> Precisión 1.0 (perfecto)
    assert calcular_precision(0, 0) == 1.0
    
    # Caso 2: Conteo manual es 0, IA > 0 -> Precisión 0.0 (error total)
    assert calcular_precision(5, 0) == 0.0
    
    # Caso 3: Coinciden -> Precisión 1.0
    assert calcular_precision(10, 10) == 1.0
    
    # Caso 4: IA contó 8 de 10 -> 1 - (2/10) = 0.8
    assert calcular_precision(8, 10) == 0.8
    
    # Caso 5: IA contó 12 de 10 -> 1 - (2/10) = 0.8
    assert calcular_precision(12, 10) == 0.8
    
    # Caso 6: IA contó 30 de 10 -> error = 20 -> 1 - 2 = -1.0 -> acotado a 0.0
    assert calcular_precision(30, 10) == 0.0

def test_procesar_imagen_sincrono_fails_if_no_model():
    # Guardar estado actual
    old_model = ml_models.get("yolo")
    if "yolo" in ml_models:
        del ml_models["yolo"]
        
    # Generar una imagen válida en memoria para que no falle por formato corrupto
    imagen_falsa = np.zeros((10, 10, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.jpg', imagen_falsa)
    fake_image_bytes = buffer.tobytes()

    with pytest.raises(RuntimeError) as exc_info:
        procesar_imagen_sincrono(fake_image_bytes)
    assert "no está cargado" in str(exc_info.value)
    
    # Restaurar
    if old_model:
        ml_models["yolo"] = old_model

def test_api_predict_success(client: TestClient):
    imagen_falsa = np.zeros((10, 10, 3), dtype=np.uint8)
    _, buffer = cv2.imencode('.jpg', imagen_falsa)
    fake_image_bytes = buffer.tobytes()

    file_payload = {"file": ("test.jpg", fake_image_bytes, "image/jpeg")}
    data_payload = {"conteo_manual": 2}
    
    response = client.post("/predict", files=file_payload, data=data_payload)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "conteo_ia" in data
    assert data["conteo_ia"] == 2
    assert data["conteo_manual"] == 2
    assert data["precision"] == 1.0
    assert len(data["detecciones"]) == 2
    assert data["tiempo_procesamiento_segundos"] >= 0

def test_api_predict_corrupt_image(client: TestClient):
    file_payload = {"file": ("test.jpg", b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;', "image/jpeg")}
    
    response = client.post("/predict", files=file_payload)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Imagen no válida" in response.json()["detail"]