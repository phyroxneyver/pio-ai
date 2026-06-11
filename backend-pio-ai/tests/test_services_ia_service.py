import json
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.models.imagenes import Imagen, ResultadoIA
from app.models.users import User
from app.services.ia_service import (
    _extraer_json,
    _normalizar_confianza,
    _precision_desde_confianza,
    _limpiar_detecciones,
    _validar_y_ajustar_conteos,
    analizar_imagen_con_ia
)

def test_extraer_json_helpers():
    # Caso 1: JSON limpio
    assert _extraer_json('{"a": 1}') == {"a": 1}
    
    # Caso 2: JSON envuelto en texto / markdown
    assert _extraer_json('texto previo {"a": 2} texto posterior') == {"a": 2}
    
    # Caso 3: JSON no válido
    with pytest.raises(json.JSONDecodeError):
        _extraer_json('no es json')

def test_normalizar_confianza():
    assert _normalizar_confianza("ALTA ") == "alta"
    assert _normalizar_confianza("media") == "media"
    assert _normalizar_confianza("invalido") == "baja"
    assert _normalizar_confianza(None) == "baja"

def test_precision_desde_confianza():
    assert _precision_desde_confianza("alta") == 0.92
    assert _precision_desde_confianza("media") == 0.72
    assert _precision_desde_confianza("baja") == 0.45

def test_limpiar_detecciones():
    raw_detections = [
        {"x": 0.5, "y": 0.6, "label": "pollito", "confidence": 0.9},  # Válido
        {"x": 0.5, "y": 0.6, "label": "pato", "confidence": 0.9},     # Label inválido
        {"x": -0.1, "y": 0.6, "label": "pollito", "confidence": 0.9}, # Coordenadas fuera de rango
        {"x": 0.5, "y": 0.6, "label": "pollito", "confidence": 0.4},  # Confianza baja
        "no_un_dict"                                                 # Formato incorrecto
    ]
    cleaned = _limpiar_detecciones(raw_detections)
    assert len(cleaned) == 1
    assert cleaned[0]["label"] == "pollito"
    assert cleaned[0]["confidence"] == 0.9

def test_validar_y_ajustar_conteos():
    detecciones = [
        {"x": 0.1, "y": 0.1, "label": "pollito"},
        {"x": 0.2, "y": 0.2, "label": "pollito"},
        {"x": 0.3, "y": 0.3, "label": "gallina"}
    ]
    
    # Imagen no válida o confianza baja
    datos_invalida = {"es_imagen_valida": False, "conteo_pollitos": 5}
    assert _validar_y_ajustar_conteos(datos_invalida, "alta", detecciones) == (0, 0, 0, 0, 0, 0)
    
    # Confianza baja
    datos_valida = {"es_imagen_valida": True, "conteo_pollitos": 5}
    assert _validar_y_ajustar_conteos(datos_valida, "baja", detecciones) == (0, 0, 0, 0, 0, 0)
    
    # Ajustar conteo según detecciones reales (el conteo no puede superar al número de cajas detectadas de esa clase)
    datos_alta = {
        "es_imagen_valida": True,
        "conteo_pollitos": 5, # Pide 5 pero solo hay 2 detectados -> ajusta a 2
        "conteo_gallinas": 1,
        "conteo_gallos": 0,
        "conteo_huevos_gallina": 0,
        "conteo_huevos_incubacion": 0,
        "conteo_huevos_rotos": 0
    }
    adjusted = _validar_y_ajustar_conteos(datos_alta, "alta", detecciones)
    assert adjusted == (2, 1, 0, 0, 0, 0)

@patch("app.services.ia_service.httpx.get")
@patch("app.services.ia_service.Groq")
def test_analizar_imagen_con_ia_service(mock_groq_class, mock_httpx_get, db_session: Session):
    # 1. Configurar Mock de Groq
    mock_groq_client = MagicMock()
    mock_groq_class.return_value = mock_groq_client
    
    mock_choice = MagicMock()
    mock_choice.message.content = json.dumps({
        "es_imagen_valida": True,
        "conteo_pollitos": 2,
        "conteo_gallinas": 1,
        "conteo_gallos": 0,
        "conteo_huevos_gallina": 3,
        "conteo_huevos_incubacion": 0,
        "conteo_huevos_rotos": 0,
        "confianza": "alta",
        "precision_estimada": 0.95,
        "notas": "Granja limpia, aves sanas.",
        "detecciones": [
            {"x": 0.1, "y": 0.1, "label": "pollito", "confidence": 0.88},
            {"x": 0.2, "y": 0.2, "label": "pollito", "confidence": 0.91},
            {"x": 0.3, "y": 0.3, "label": "gallina", "confidence": 0.85},
            {"x": 0.4, "y": 0.4, "label": "huevo_gallina", "confidence": 0.75},
            {"x": 0.4, "y": 0.5, "label": "huevo_gallina", "confidence": 0.77},
            {"x": 0.4, "y": 0.6, "label": "huevo_gallina", "confidence": 0.79}
        ]
    })
    
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_groq_client.chat.completions.create.return_value = mock_response
    
    # 2. Configurar Mock de HTTPX
    mock_http_response = MagicMock()
    mock_http_response.content = b"fake_image_bytes"
    mock_http_response.status_code = 200
    mock_httpx_get.return_value = mock_http_response
    
    # 3. Guardar registros iniciales en BD de pruebas
    user = User(email="ia_test@test.com", hashed_password="pw", role="usuario")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    img = Imagen(
        nombre_original="test.jpg",
        nombre_almacenado="test_stored.jpg",
        ruta="https://cloudinary.com/test.jpg",
        content_type="image/jpeg",
        tamaño_bytes=1000,
        hash_archivo="unique_hash",
        usuario_id=user.id
    )
    db_session.add(img)
    db_session.flush() # Obtener id
    
    res = ResultadoIA(imagen_id=img.id, estado="pendiente")
    db_session.add(res)
    db_session.commit()
    
    # 4. Ejecutar análisis
    resultado = analizar_imagen_con_ia(db_session, img.id)
    
    # 5. Aseveraciones
    assert resultado.estado == "completado"
    assert resultado.conteo_pollitos == 2
    assert resultado.confianza == "alta"
    assert resultado.precision_estimada == 0.95
    assert resultado.error_detalle is None
    
    # Validar que las notas se parsearon a JSON y guardaron correctamente
    notas = json.loads(resultado.notas_ia)
    assert notas["conteo_gallinas"] == 1
    assert notas["conteo_huevos"] == 3
    assert "Granja limpia" in notas["notas"]
    
    # Validar detecciones
    detecciones = json.loads(resultado.detecciones_json)
    assert len(detecciones) == 6
    assert detecciones[0]["label"] == "pollito"
