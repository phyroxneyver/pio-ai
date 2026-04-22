from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

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
    usuario = relationship("User", backref="imagenes")


class ResultadoIA(Base):
    __tablename__ = "resultados_ia"

    id = Column(Integer, primary_key=True, index=True)
    imagen_id = Column(Integer, ForeignKey("imagenes.id", ondelete="CASCADE"), unique=True, nullable=False)
    conteo_pollitos = Column(Integer, nullable=True)
    confianza = Column(String(20), nullable=True)
    estado = Column(String(20), nullable=False, default="pendiente")
    error_detalle = Column(Text, nullable=True)
    procesado_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    coordenadas = Column(Text, nullable=True)

    imagen = relationship("Imagen", back_populates="resultado_ia")