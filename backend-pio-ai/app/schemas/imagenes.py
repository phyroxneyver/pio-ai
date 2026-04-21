"""
Schemas Pydantic para el módulo de imágenes.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List


# ---------------------------------------------------------------------------
# Resultado IA (sub-schema)
# ---------------------------------------------------------------------------
class ResultadoIAResponse(BaseModel):
    id: int
    imagen_id: int
    conteo_pollitos: Optional[int]
    confianza: Optional[str]
    estado: str
    error_detalle: Optional[str]
    procesado_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


# ---------------------------------------------------------------------------
# Imagen
# ---------------------------------------------------------------------------
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
    """Respuesta paginada / listado."""
    total: int
    imagenes: List[ImagenResponse]


class ImagenDeleteResponse(BaseModel):
    detail: str
    imagen_id: int
