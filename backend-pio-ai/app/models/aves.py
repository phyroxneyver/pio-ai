from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class Ave(Base):
    __tablename__ = "aves"

    id = Column(Integer, primary_key=True, index=True)
    tipo = Column(String(50), nullable=False)         
    cantidad = Column(Integer, nullable=False)
    raza = Column(String(100), nullable=True)
    fecha_ingreso = Column(DateTime, default=datetime.utcnow)
    notas = Column(String(500), nullable=True)

    producciones = relationship("ProduccionHuevos", back_populates="ave")


class ProduccionHuevos(Base):
    __tablename__ = "produccion_huevos"

    id = Column(Integer, primary_key=True, index=True)
    ave_id = Column(Integer, ForeignKey("aves.id"), nullable=False)
    cantidad_huevos = Column(Integer, nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    notas = Column(String(500), nullable=True)

    ave = relationship("Ave", back_populates="producciones")