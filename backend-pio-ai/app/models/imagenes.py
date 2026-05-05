"""
Modelo de imágenes para monitoreo avícola.
"""
import json
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from ..core.database import Base


class Imagen(Base):
    __tablename__ = "imagenes"

    id = Column(Integer, primary_key=True, index=True)
    nombre_original = Column(String(255), nullable=False)
    nombre_almacenado = Column(String(255), unique=True, nullable=False)
    ruta = Column(String(500), nullable=False)
    content_type = Column(String(50), nullable=False)
    tamaño_bytes = Column(Integer, nullable=False)
    hash_archivo = Column(String(64), unique=True, nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    resultado_ia = relationship(
        "ResultadoIA",
        back_populates="imagen",
        uselist=False,
        cascade="all, delete-orphan",
    )
    feedbacks = relationship(
        "FeedbackIA",
        back_populates="imagen",
        cascade="all, delete-orphan",
        order_by="FeedbackIA.created_at.desc()",
    )
    usuario = relationship("User", backref="imagenes")


class ResultadoIA(Base):
    """Resultado del análisis IA asociado a una imagen."""

    __tablename__ = "resultados_ia"

    id = Column(Integer, primary_key=True, index=True)
    imagen_id = Column(
        Integer,
        ForeignKey("imagenes.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    conteo_pollitos = Column(Integer, nullable=True)
    confianza = Column(String(20), nullable=True)
    estado = Column(String(20), nullable=False, default="pendiente")
    error_detalle = Column(Text, nullable=True)
    procesado_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    coordenadas = Column(Text, nullable=True)
    duracion_ms = Column(Integer, nullable=True)
    precision_estimada = Column(Float, nullable=True)
    notas_ia = Column(Text, nullable=True)
    detecciones_json = Column(Text, nullable=True)

    imagen = relationship("Imagen", back_populates="resultado_ia")

    @property
    def detecciones(self) -> list[dict]:
        # Priorizamos el campo 'coordenadas' solicitado
        raw_data = self.coordenadas or self.detecciones_json
        if not raw_data:
            return []
        try:
            data = json.loads(raw_data)
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []


class FeedbackIA(Base):
    """Corrección manual del trabajador."""

    __tablename__ = "feedback_ia"

    id = Column(Integer, primary_key=True, index=True)
    imagen_id = Column(
        Integer,
        ForeignKey("imagenes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resultado_ia_id = Column(
        Integer,
        ForeignKey("resultados_ia.id", ondelete="SET NULL"),
        nullable=True,
    )
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    conteo_ia = Column(Integer, nullable=True)
    conteo_corregido = Column(Integer, nullable=False)
    diferencia = Column(Integer, nullable=False)
    tipo_feedback = Column(String(30), nullable=False, default="correccion")
    motivo = Column(Text, nullable=True)
    imagen_url = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    imagen = relationship("Imagen", back_populates="feedbacks")
    resultado_ia = relationship("ResultadoIA")
    usuario = relationship("User", backref="feedbacks_ia")