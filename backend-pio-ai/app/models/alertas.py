"""
Modelos para el sistema de alertas y notificaciones avícolas.

- Alerta: evento del sistema (mortalidad, temperatura, producción baja, etc.)
- NotificacionInterna: notificación dirigida a un usuario específico
- HistorialAlerta: registro inmutable de cada cambio de estado (trazabilidad)
"""
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Boolean,
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


class Alerta(Base):
    """
    Alerta del sistema IoT avícola.

    Estados posibles: activa → leida → atendida
    Prioridades: baja | media | alta | critica
    """
    __tablename__ = "alertas"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False, index=True)
    # Tipos: mortalidad | temperatura | produccion_baja | alimentacion | otro
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=False)
    prioridad = Column(String(20), nullable=False, default="media")
    # baja | media | alta | critica
    estado = Column(String(20), nullable=False, default="activa", index=True)
    # activa | leida | atendida
    creado_por_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    atendido_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    justificacion_cierre = Column(Text, nullable=True)
    eliminada = Column(Boolean, default=False, nullable=False)
    justificacion_eliminacion = Column(Text, nullable=True)
    eliminada_por_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    eliminada_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relaciones
    creado_por = relationship(
        "User", foreign_keys=[creado_por_id], backref="alertas_creadas",
    )
    atendido_por = relationship(
        "User", foreign_keys=[atendido_por_id],
    )
    eliminada_por = relationship(
        "User", foreign_keys=[eliminada_por_id],
    )
    historial = relationship(
        "HistorialAlerta",
        back_populates="alerta",
        order_by="HistorialAlerta.created_at.desc()",
        cascade="all, delete-orphan",
    )
    notificaciones = relationship(
        "NotificacionInterna",
        back_populates="alerta",
        cascade="all, delete-orphan",
    )


class NotificacionInterna(Base):
    """Notificación dirigida a un usuario sobre una alerta."""
    __tablename__ = "notificaciones_internas"

    id = Column(Integer, primary_key=True, index=True)
    alerta_id = Column(
        Integer, ForeignKey("alertas.id", ondelete="CASCADE"), nullable=False,
    )
    usuario_id = Column(
        Integer, ForeignKey("users.id"), nullable=False, index=True,
    )
    leida = Column(Boolean, default=False, nullable=False)
    leida_at = Column(DateTime, nullable=True)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
    )

    # Relaciones
    alerta = relationship("Alerta", back_populates="notificaciones")
    usuario = relationship("User", backref="notificaciones")


class HistorialAlerta(Base):
    """
    Registro inmutable de cambios en una alerta.
    Garantiza trazabilidad completa: quién hizo qué y cuándo.
    """
    __tablename__ = "historial_alertas"

    id = Column(Integer, primary_key=True, index=True)
    alerta_id = Column(
        Integer, ForeignKey("alertas.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    accion = Column(String(50), nullable=False)
    # creada | leida | atendida | eliminada
    estado_anterior = Column(String(20), nullable=True)
    estado_nuevo = Column(String(20), nullable=True)
    detalle = Column(Text, nullable=True)
    realizado_por_id = Column(
        Integer, ForeignKey("users.id"), nullable=False,
    )
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc),
    )

    # Relaciones
    alerta = relationship("Alerta", back_populates="historial")
    realizado_por = relationship("User")
