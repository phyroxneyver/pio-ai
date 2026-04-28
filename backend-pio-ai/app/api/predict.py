import asyncio
import cv2
import numpy as np
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from pydantic import BaseModel
from typing import Optional, List

from ..core.ml import ml_models

router = APIRouter(prefix="/predict", tags=["Inferencia IA"])

class Detection(BaseModel):
    clase: str
    confianza: float
    bbox: List[float]

class PredictResponse(BaseModel):
    conteo_ia: int
    conteo_manual: Optional[int] = None
    precision: Optional[float] = None
    detecciones: List[Detection]
    tiempo_procesamiento_segundos: float

def calcular_precision(conteo_ia: int, conteo_manual: int) -> float:
    """Calcula la precisión basada en la fórmula: 1 - (|IA - Manual| / Manual)"""
    if conteo_manual == 0:
        return 0.0 if conteo_ia > 0 else 1.0
    
    error = abs(conteo_ia - conteo_manual)
    precision = 1.0 - (error / conteo_manual)
    return max(0.0, round(precision, 4))

def procesar_imagen_sincrono(image_bytes: bytes, conteo_manual: int = None) -> dict:
    """
    Lógica de inferencia bloqueante. Se ejecutará en un hilo separado.
    """
    start_time = time.time()
    
    # Decodificar y redimensionar con OpenCV (Optimización)
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Imagen no válida o corrupta.")
    
    # Redimensionar para inferencia rápida
    img_resized = cv2.resize(img, (640, 640))
    
    modelo = ml_models.get("yolo")
    if not modelo:
        raise RuntimeError("El modelo no está cargado.")
        
    # Inferencia mock - AQUÍ SE LLAMARÍA AL MODELO REAL
    mock_results = [
        {"clase": "pollito", "confianza": 0.85, "bbox": [10, 10, 50, 50]},
        {"clase": "pollito", "confianza": 0.92, "bbox": [100, 100, 150, 150]},
        {"clase": "pollito", "confianza": 0.45, "bbox": [200, 200, 250, 250]}, # Será filtrado
    ]
    
    # Filtro de Confianza > 0.50
    detecciones_validas = [
        Detection(**det) for det in mock_results if det["confianza"] > 0.50
    ]
    
    conteo_ia = len(detecciones_validas)
    
    precision = None
    if conteo_manual is not None:
        precision = calcular_precision(conteo_ia, conteo_manual)
        
    tiempo_procesamiento = round(time.time() - start_time, 3)
    
    return {
        "conteo_ia": conteo_ia,
        "conteo_manual": conteo_manual,
        "precision": precision,
        "detecciones": detecciones_validas,
        "tiempo_procesamiento_segundos": tiempo_procesamiento
    }

@router.post("", response_model=PredictResponse, summary="Inferencia de imágenes avícolas (YOLO)")
async def predict_image(
    file: UploadFile = File(..., description="Imagen a analizar (JPG/PNG)"),
    conteo_manual: Optional[int] = Form(None, description="Conteo manual realizado por el usuario (Opcional)")
):
    """
    Endpoint de inferencia que no bloquea el event loop.
    Procesa la imagen asíncronamente en un hilo secundario y devuelve un JSON estructurado.
    """
    try:
        image_bytes = await file.read()
        
        # Inferencia asíncrona
        resultado = await asyncio.to_thread(
            procesar_imagen_sincrono,
            image_bytes,
            conteo_manual
        )
        
        return PredictResponse(**resultado)
        
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error en inferencia: {str(e)}")
