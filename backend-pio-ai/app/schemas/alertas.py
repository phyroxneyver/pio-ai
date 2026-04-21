"""
Schemas Pydantic para el módulo de alertas y notificaciones.
"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal, List


# ---------------------------------------------------------------------------
# Alertas
# ---------------------------------------------------------------------------
class AlertaCreate(BaseModel):
    tipo: Literal[
        "mortalidad", "temperatura", "produccion_baja", "alimentacion", "otro"
    ] = Field(..., description="Tipo de alerta")
    titulo: str = Field(
        ..., min_length=3, max_length=200, description="Título descriptivo",
    )
    descripcion: str = Field(
        ..., min_length=5, description="Descripción detallada de la alerta",
    )
    prioridad: Literal["baja", "media", "alta", "critica"] = Field(
        "media", description="Nivel de prioridad",
    )


class AlertaMarcarLeida(BaseModel):
    """Body vacío — la acción es implícita."""
    pass


class AlertaAtender(BaseModel):
    justificacion: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Justificación de la atención (mín. 10 caracteres)",
    )


class AlertaEliminar(BaseModel):
    justificacion: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Justificación obligatoria para eliminar (mín. 10 caracteres)",
    )


class AlertaResponse(BaseModel):
    id: int
    tipo: str
    titulo: str
    descripcion: str
    prioridad: str
    estado: str
    creado_por_id: int
    atendido_por_id: Optional[int]
    justificacion_cierre: Optional[str]
    eliminada: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AlertaListResponse(BaseModel):
    total: int
    alertas: List[AlertaResponse]


# ---------------------------------------------------------------------------
# Notificaciones internas
# ---------------------------------------------------------------------------
class NotificacionResponse(BaseModel):
    id: int
    alerta_id: int
    usuario_id: int
    leida: bool
    leida_at: Optional[datetime]
    created_at: datetime

    # Info básica de la alerta anidada
    alerta: Optional[AlertaResponse] = None

    class Config:
        from_attributes = True


class NotificacionListResponse(BaseModel):
    total: int
    no_leidas: int
    notificaciones: List[NotificacionResponse]


# ---------------------------------------------------------------------------
# Historial de alertas (trazabilidad)
# ---------------------------------------------------------------------------
class HistorialEntrada(BaseModel):
    id: int
    alerta_id: int
    accion: str
    estado_anterior: Optional[str]
    estado_nuevo: Optional[str]
    detalle: Optional[str]
    realizado_por_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class HistorialResponse(BaseModel):
    alerta_id: int
    total: int
    entradas: List[HistorialEntrada]
