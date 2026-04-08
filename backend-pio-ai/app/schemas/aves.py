from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Literal


# ---------- Aves ----------

class AveCreate(BaseModel):
    tipo: Literal["pollito", "gallina"] = Field(..., description="Tipo de ave: 'pollito' o 'gallina'")
    cantidad: int = Field(..., gt=0, description="Cantidad de aves")
    raza: Optional[str] = None
    notas: Optional[str] = None


class AveResponse(BaseModel):
    id: int
    tipo: str
    cantidad: int
    raza: Optional[str]
    fecha_ingreso: datetime
    notas: Optional[str]

    class Config:
        from_attributes = True


# ---------- Producción de huevos ----------

class ProduccionCreate(BaseModel):
    ave_id: int = Field(..., description="ID del ave asociada")
    cantidad_huevos: int = Field(..., gt=0, description="Cantidad de huevos producidos")
    notas: Optional[str] = None


class ProduccionResponse(BaseModel):
    id: int
    ave_id: int
    cantidad_huevos: int
    fecha: datetime
    notas: Optional[str]

    class Config:
        from_attributes = True