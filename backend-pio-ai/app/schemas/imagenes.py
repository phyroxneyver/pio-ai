"""
Schemas Pydantic para el módulo de imágenes.
"""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class DeteccionVisual(BaseModel):
    x: float = Field(..., ge=0, le=1, description="Posición horizontal normalizada de 0 a 1")
    y: float = Field(..., ge=0, le=1, description="Posición vertical normalizada de 0 a 1")
    label: Optional[str] = "pollito"
    confidence: Optional[float] = Field(None, ge=0, le=1)


class ResultadoIAResponse(BaseModel):
    id: int
    imagen_id: int
    conteo_pollitos: Optional[int]
    confianza: Optional[str]
    estado: str
    error_detalle: Optional[str]
    procesado_at: Optional[datetime]
    created_at: datetime

    duracion_ms: Optional[int] = None
    precision_estimada: Optional[float] = None
    notas_ia: Optional[str] = None
    detecciones: List[DeteccionVisual] = []

    class Config:
        from_attributes = True


class ImagenResponse(BaseModel):
    id: int
    nombre_original: str
    nombre_almacenado: str
    ruta: str
    content_type: str
    tamaño_bytes: int = Field(..., alias="tamaño_bytes")
    hash_archivo: str
    usuario_id: int
    created_at: datetime
    resultado_ia: Optional[ResultadoIAResponse] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class ImagenListResponse(BaseModel):
    total: int
    imagenes: List[ImagenResponse]


class ImagenDeleteResponse(BaseModel):
    detail: str
    imagen_id: int


class FeedbackIACreate(BaseModel):
    conteo_corregido: int = Field(..., ge=0)
    tipo_feedback: Literal["correccion", "fallida"] = "correccion"
    motivo: Optional[str] = Field(None, max_length=1000)


class FeedbackIAResponse(BaseModel):
    id: int
    imagen_id: int
    resultado_ia_id: Optional[int]
    usuario_id: int
    conteo_ia: Optional[int]
    conteo_corregido: int
    diferencia: int
    tipo_feedback: str
    motivo: Optional[str]
    imagen_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class UltimaMetricaIAResponse(BaseModel):
    imagen_id: int
    resultado_id: int
    conteo_pollitos: Optional[int]
    confianza: Optional[str]
    estado: str
    duracion_ms: Optional[int]
    precision_estimada: Optional[float]
    notas_ia: Optional[str]
    procesado_at: Optional[datetime]
    imagen_url: str